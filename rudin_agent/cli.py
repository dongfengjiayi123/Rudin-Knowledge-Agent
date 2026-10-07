import argparse
import asyncio
import json
from .config import ROOT,PDF_PATH
from .store import Store

def main():
    p=argparse.ArgumentParser(description='Rudin knowledge agent')
    sub=p.add_subparsers(dest='cmd',required=True)
    serve=sub.add_parser('serve'); serve.add_argument('--port',type=int,default=8000)
    sub.add_parser('init'); sub.add_parser('stats')
    ask=sub.add_parser('ask'); ask.add_argument('question')
    ex=sub.add_parser('extract'); ex.add_argument('--id'); ex.add_argument('--chapter',type=int); ex.add_argument('--all',action='store_true'); ex.add_argument('--limit',type=int,default=10)
    sub.add_parser('proposals')
    rv=sub.add_parser('review'); rv.add_argument('id'); rv.add_argument('--approve',action='store_true')
    sub.add_parser('embed')
    export=sub.add_parser('export'); export.add_argument('--output',default='data/export.json')
    sub.add_parser('reindex')
    args=p.parse_args()
    if args.cmd=='serve':
        import uvicorn
        uvicorn.run('rudin_agent.api:app',host='127.0.0.1',port=args.port)
        return
    s=Store().initialize()
    try:
        if args.cmd in ('init','stats'): print(json.dumps(s.stats(),ensure_ascii=False,indent=2))
        elif args.cmd=='ask':
            from .agent import Agent
            print(json.dumps(asyncio.run(Agent(s).ask(args.question)),ensure_ascii=False,indent=2))
        elif args.cmd=='extract':
            from .extract import enrich,proposals
            done={v['node']['id'] for v in proposals(s)}
            candidates=[n for n in s.nodes() if n['id'] not in done and n['status']=='indexed' and (not args.id or n['id']==args.id) and (not args.chapter or n['chapter']==args.chapter)]
            if args.id: candidates=[s.node(args.id)] if s.node(args.id) else []
            if not (args.id or args.chapter or args.all): p.error('请选择 --id、--chapter 或 --all')
            async def run():
                for n in candidates[:args.limit]:
                    try: print(json.dumps(await enrich(s,n['id']),ensure_ascii=False))
                    except Exception as exc: print(json.dumps({'id':n['id'],'error':type(exc).__name__},ensure_ascii=False))
            asyncio.run(run())
        elif args.cmd=='proposals':
            from .extract import proposals
            print(json.dumps(proposals(s),ensure_ascii=False,indent=2))
        elif args.cmd=='review':
            from .extract import review
            print(json.dumps(review(s,args.id,args.approve),ensure_ascii=False))
        elif args.cmd=='embed':
            from .providers import OpenAICompatibleEmbedding
            async def run():
                provider=OpenAICompatibleEmbedding()
                if not provider.configured: raise ValueError('请先填写 EMBED_* 配置')
                nodes=s.nodes()
                for i in range(0,len(nodes),16):
                    batch=nodes[i:i+16]
                    vs=await provider.embed([n['title']+'\n'+n['statement'] for n in batch])
                    if len(vs)!=len(batch): raise ValueError('Embedding count mismatch')
                    for n,v in zip(batch,vs): s.set_vector(n['id'],provider.model,v)
                    print(f'Indexed {min(i+16,len(nodes))}/{len(nodes)}')
            asyncio.run(run())
        elif args.cmd=='export':
            from pathlib import Path
            dst=Path(args.output); dst.parent.mkdir(parents=True,exist_ok=True)
            dst.write_text(json.dumps({'nodes':s.nodes(),'edges':s.edges(True)},ensure_ascii=False,indent=2),'utf8'); print(dst.resolve())
        elif args.cmd=='reindex':
            from .ingest import parse_pdf
            index=parse_pdf(PDF_PATH)
            with s.db:
                for table in ['edges','nodes','pages','metadata','vectors']: s.db.execute('DELETE FROM '+table)
            s.load(index)
            original=json.loads((ROOT/'data/index.json').read_text('utf8'))
            if index['book']['sha256']==original['book']['sha256']: s.load(json.loads((ROOT/'data/curated.json').read_text('utf8')))
            print(json.dumps(s.stats(),ensure_ascii=False))
    finally: s.close()

if __name__=='__main__': main()
