"""Shared application tools, used by HTTP, the Agent and MCP."""
import asyncio
from .providers import OpenAICompatibleEmbedding

class KnowledgeTools:
    def __init__(self,store): self.store=store
    def search_knowledge(self,query:str,limit:int=8): return self.store.search(query,limit)
    def get_knowledge_point(self,id:str):
        result=self.store.related(id)
        # Include all definitions in the same numbered entry (e.g. 2.18).
        ref=result['node']['ref']
        result['same_entry_definitions']=[n for n in self.store.nodes() if n['ref']==ref and n['kind']=='definition' and n['id']!=id]
        return result
    def get_neighborhood(self,id:str,depth:int=1): return self.store.graph(id,depth)
    def find_dependency_path(self,start:str,end:str):
        return {'direction':'dependent → prerequisite','path':self.store.path(start,end)}
    def read_source(self,pdf_page:int):
        p=self.store.page(pdf_page)
        if not p: raise KeyError('PDF page not found')
        return p
    def search_source(self,query:str,limit:int=3): return self.store.search_pages(query,limit)
    async def hybrid_search(self,query,limit=8):
        lexical=self.store.search(query,limit)
        embed=OpenAICompatibleEmbedding()
        if not embed.configured: return lexical
        vector=(await embed.embed([query]))[0]
        semantic=self.store.vector_search(vector,embed.model,limit)
        # Reciprocal rank fusion; different score ranges remain comparable.
        scores={}; nodes={}
        for items in [lexical,semantic]:
            for rank,n in enumerate(items):
                scores[n['id']]=scores.get(n['id'],0)+1/(60+rank+1); nodes[n['id']]=n
        return [dict(nodes[id],score=score) for id,score in sorted(scores.items(),key=lambda x:-x[1])[:limit]]

PARAMS={
 'search_knowledge':('检索定义、定理和教材条目',{'query':{'type':'string'},'limit':{'type':'integer','minimum':1,'maximum':20}},['query']),
 'get_knowledge_point':('读取知识点、相关定义和涉及它的定理',{'id':{'type':'string'}},['id']),
 'get_neighborhood':('获取知识点关系图，区分引用和证明依赖',{'id':{'type':'string'},'depth':{'type':'integer','minimum':0,'maximum':2}},['id']),
 'find_dependency_path':('按有向依赖边追溯定理所需的先修知识',{'start':{'type':'string'},'end':{'type':'string'}},['start','end']),
 'read_source':('读取教材 PDF 页原文以核对证据和条件',{'pdf_page':{'type':'integer','minimum':1}},['pdf_page']),
 'search_source':('检索全书 PDF 页原文；英文词检索更准确',{'query':{'type':'string'},'limit':{'type':'integer','minimum':1,'maximum':5}},['query'])}
TOOL_SCHEMAS=[{'type':'function','function':{'name':name,'description':description,'parameters':{'type':'object','properties':props,'required':required,'additionalProperties':False}}} for name,(description,props,required) in PARAMS.items()]

async def dispatch(tools,name,args):
    if name not in PARAMS: raise ValueError('Unknown tool')
    _,props,required=PARAMS[name]
    if not isinstance(args,dict) or set(args)-set(props) or set(required)-set(args): raise ValueError('Invalid tool arguments')
    for k,v in args.items():
        p=props[k]
        if p['type']=='integer' and (type(v)!=int or v<p.get('minimum',v) or v>p.get('maximum',v)): raise ValueError('Invalid integer')
        if p['type']=='string' and (not isinstance(v,str) or not v.strip() or len(v)>2000): raise ValueError('Invalid string')
    if name=='search_knowledge': return await tools.hybrid_search(**args)
    return getattr(tools,name)(**args)
