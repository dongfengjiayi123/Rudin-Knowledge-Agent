"""SQLite adapter: JSON knowledge, directed graph, full-text pages and optional vectors.
Swap this class with another adapter implementing the same methods for Neo4j/Qdrant.
"""
import json
import math
import re
import sqlite3
from collections import deque
from .config import DB_PATH, ROOT

RELATIONS = {'uses_definition','depends_on','references','specializes','equivalent_to','implies'}
STATUSES = {'indexed','reviewed','pending'}

def tokens(text):
    text = text.lower()
    return set(re.findall(r'\d+\.\d+|[a-z]+|[\u4e00-\u9fff]{1,}',text)) | {text[i:i+2] for i in range(len(text)-1) if '\u4e00' <= text[i] <= '\u9fff' and '\u4e00' <= text[i+1] <= '\u9fff'}

class Store:
    def __init__(self, path=DB_PATH):
        self.db_path = str(path)
        if self.db_path != ':memory:':
            from pathlib import Path
            Path(self.db_path).parent.mkdir(parents=True,exist_ok=True)
        self.db = sqlite3.connect(self.db_path, check_same_thread=False)
        self.db.row_factory = sqlite3.Row
        self.db.executescript('''
        PRAGMA journal_mode=WAL;
        CREATE TABLE IF NOT EXISTS nodes(id TEXT PRIMARY KEY, payload TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS edges(source TEXT,target TEXT,relation TEXT,payload TEXT,PRIMARY KEY(source,target,relation));
        CREATE TABLE IF NOT EXISTS pages(number INTEGER PRIMARY KEY,payload TEXT);
        CREATE TABLE IF NOT EXISTS metadata(key TEXT PRIMARY KEY,payload TEXT);
        CREATE TABLE IF NOT EXISTS vectors(id TEXT PRIMARY KEY,model TEXT,vector TEXT);
        ''')
    def close(self): self.db.close()
    def put_node(self,node):
        if not isinstance(node.get('id'),str) or not node['id'] or node.get('kind') not in {'definition','theorem','example','remark'} or node.get('status') not in STATUSES:
            raise ValueError('Invalid node schema')
        if not node.get('statement') or not isinstance(node.get('chapter'),int) or not 1<=node['chapter']<=11:
            raise ValueError('Statement and chapter required')
        source = node.get('source',{})
        if not isinstance(source.get('pdf_page'),int) or source['pdf_page']<1:
            raise ValueError('Source PDF page is required')
        old = self.node(node['id'])
        if old and (old['statement'] != node['statement'] or old['title'] != node['title']):
            self.db.execute('DELETE FROM vectors WHERE id=?', (node['id'],))
        self.db.execute('INSERT OR REPLACE INTO nodes VALUES(?,?)',(node['id'],json.dumps(node,ensure_ascii=False)))
    def put_edge(self,edge):
        if edge.get('relation') not in RELATIONS or edge.get('status') not in STATUSES or not edge.get('evidence'):
            raise ValueError('Invalid relationship schema')
        if edge['source']==edge['target'] or not self.node(edge['source']) or not self.node(edge['target']):
            raise ValueError('Relationship endpoints must exist and differ')
        self.db.execute('INSERT OR REPLACE INTO edges VALUES(?,?,?,?)',(edge['source'],edge['target'],edge['relation'],json.dumps(edge,ensure_ascii=False)))
    def node(self,id):
        r=self.db.execute('SELECT payload FROM nodes WHERE id=?',(id,)).fetchone()
        return json.loads(r[0]) if r else None
    def nodes(self): return [json.loads(r[0]) for r in self.db.execute('SELECT payload FROM nodes')]
    def edges(self,include_pending=False):
        all_edges=[json.loads(r[0]) for r in self.db.execute('SELECT payload FROM edges')]
        return [e for e in all_edges if include_pending or e['status']!='pending']
    def load(self,payload):
        with self.db:
            for n in payload['nodes']: self.put_node(n)
            for e in payload['edges']: self.put_edge(e)
            for p in payload.get('pages',[]):
                self.db.execute('INSERT OR REPLACE INTO pages VALUES(?,?)',(p['pdf_page'],json.dumps(p,ensure_ascii=False)))
            if 'book' in payload: self.db.execute('INSERT OR REPLACE INTO metadata VALUES(?,?)',('book',json.dumps(payload['book'],ensure_ascii=False)))
    def initialize(self):
        if not self.nodes():
            self.load(json.loads((ROOT/'data/index.json').read_text('utf8')))
            self.load(json.loads((ROOT/'data/curated.json').read_text('utf8')))
        return self
    def search(self,query,limit=10):
        q=tokens(query)
        results=[]
        for n in self.nodes():
            title=' '.join([n['title'],n['id']]+n.get('aliases',[])).lower()
            body=(title+' '+n['statement']).lower()
            score=sum(8 if t in title else 1 for t in q if t in body)
            if query.lower().strip() in title and query.strip(): score+=20
            if score: results.append((score,n))
        return [dict(n,score=s) for s,n in sorted(results,key=lambda x:(-x[0],x[1]['id']))[:max(1,min(limit,50))]]
    def graph(self,id,depth=1,include_pending=False):
        if not self.node(id): raise KeyError(id)
        depth=max(0,min(depth,3))
        edges=self.edges(include_pending)
        seen={id}; frontier={id}
        for _ in range(depth):
            new={v for e in edges if e['source'] in frontier or e['target'] in frontier for v in [e['source'],e['target']]}-seen
            seen|=new; frontier=new
        return {'nodes':[n for n in self.nodes() if n['id'] in seen], 'edges':[e for e in edges if e['source'] in seen and e['target'] in seen]}
    def related(self,id):
        if not self.node(id): raise KeyError(id)
        incoming=[]; outgoing=[]
        for e in self.edges():
            if e['source']==id: outgoing.append(dict(e,node=self.node(e['target'])))
            if e['target']==id: incoming.append(dict(e,node=self.node(e['source'])))
        return {'node':self.node(id),'incoming':incoming,'outgoing':outgoing}
    def path(self,start,end,relations=None):
        allowed=set(relations or ['depends_on','uses_definition'])
        if not allowed<=RELATIONS: raise ValueError('Unknown relation')
        if not self.node(start) or not self.node(end): raise KeyError('Missing endpoint')
        q=deque([(start,[start])]); seen={start}
        edges=self.edges()
        while q:
            cur,path=q.popleft()
            if cur==end: return path
            for e in edges:
                if e['source']==cur and e['relation'] in allowed and e['target'] not in seen:
                    seen.add(e['target']); q.append((e['target'],path+[e['target']]))
        return []
    def page(self,number):
        r=self.db.execute('SELECT payload FROM pages WHERE number=?',(number,)).fetchone()
        return json.loads(r[0]) if r else None
    def search_pages(self,query,limit=5):
        q=tokens(query); results=[]
        for r in self.db.execute('SELECT payload FROM pages'):
            p=json.loads(r[0]); score=sum(t in p['text'].lower() for t in q)
            if score: results.append(dict(p,score=score))
        return sorted(results,key=lambda p:-p['score'])[:max(1,min(limit,10))]
    def stats(self):
        ns=self.nodes(); es=self.edges(True)
        book=self.db.execute('SELECT payload FROM metadata WHERE key="book"').fetchone()
        return {'nodes':len(ns),'edges':len(es),'reviewed':sum(n['status']=='reviewed' for n in ns),'pending':sum(n['status']=='pending' for n in ns),'pages':self.db.execute('SELECT COUNT(*) FROM pages').fetchone()[0], 'book':json.loads(book[0]) if book else {}}
    def set_vector(self,id,model,vector):
        if not vector or not all(isinstance(v,(int,float)) and math.isfinite(v) for v in vector): raise ValueError('Invalid vector')
        self.db.execute('INSERT OR REPLACE INTO vectors VALUES(?,?,?)',(id,model,json.dumps(vector))); self.db.commit()
    def vector_search(self,query_vector,model,limit=10):
        results=[]
        for r in self.db.execute('SELECT id,vector FROM vectors WHERE model=?',(model,)):
            v=json.loads(r['vector'])
            if len(v)!=len(query_vector): continue
            den=math.sqrt(sum(x*x for x in v)*sum(x*x for x in query_vector))
            if den and self.node(r['id']): results.append((sum(a*b for a,b in zip(v,query_vector))/den,self.node(r['id'])))
        return [dict(n,score=s) for s,n in sorted(results,key=lambda x:-x[0])[:limit]]
