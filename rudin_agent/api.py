from contextlib import asynccontextmanager
import json
import os
from urllib.parse import urlsplit
from fastapi import FastAPI,Depends,HTTPException,Query,Request
from fastapi.responses import FileResponse,JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel,Field
from .config import ROOT,PDF_PATH
from .store import Store
from .agent import Agent
from .providers import OpenAICompatibleChat,OpenAICompatibleEmbedding
from .extract import enrich,proposals,review
from .ingest import CHAPTERS

@asynccontextmanager
async def lifespan(app):
    s=Store().initialize(); s.close()
    yield
app=FastAPI(title='Rudin Knowledge Agent',version='0.1.0',lifespan=lifespan)

def db():
    s=Store()
    try: yield s
    finally: s.close()

@app.middleware('http')
async def origin_guard(request:Request,call_next):
    origin=request.headers.get('origin')
    if request.method not in {'GET','HEAD','OPTIONS'} and origin:
        expected=f'{request.url.scheme}://{request.headers.get("host","")}'
        if origin!=expected: return JSONResponse({'detail':'Cross-origin write rejected'},status_code=403)
    return await call_next(request)

@app.exception_handler(KeyError)
async def missing(request,exc): return JSONResponse({'detail':'条目不存在'},status_code=404)

class Ask(BaseModel): question:str=Field(min_length=1,max_length=2000)
class Review(BaseModel): approve:bool

@app.get('/api/status')
def status(s=Depends(db)):
    return dict(s.stats(),llm_configured=OpenAICompatibleChat().configured,embedding_configured=OpenAICompatibleEmbedding().configured,chapters=CHAPTERS)
@app.get('/api/concepts')
def concepts(q:str='',chapter:int|None=Query(None,ge=1,le=11),kind:str|None=None,reviewed:bool=False,s=Depends(db)):
    ns=s.search(q,50) if q.strip() else s.nodes()
    ns=[n for n in ns if (not chapter or n['chapter']==chapter) and (not kind or n['kind']==kind) and (not reviewed or n['status']=='reviewed')]
    return [{k:v for k,v in n.items() if k!='raw'} for n in (ns if q.strip() else sorted(ns,key=lambda n:tuple(int(v) if v.isdigit() else v for v in n['id'].split('.'))))]
@app.get('/api/concepts/{id}')
def concept(id:str,s=Depends(db)):
    from .tools import KnowledgeTools
    return KnowledgeTools(s).get_knowledge_point(id)
@app.get('/api/graph/{id}')
def graph(id:str,depth:int=Query(1,ge=0,le=3),s=Depends(db)): return s.graph(id,depth)
@app.get('/api/path')
def path(start:str,end:str,s=Depends(db)): return {'path':s.path(start,end),'direction':'dependent → prerequisite'}
@app.get('/api/source/{number}')
def source(number:int,s=Depends(db)):
    result=s.page(number)
    if not result: raise KeyError(number)
    return result
@app.get('/api/book')
def book():
    if not PDF_PATH.is_file(): raise HTTPException(404,'未找到教材，请检查 RUDIN_PDF')
    return FileResponse(PDF_PATH,media_type='application/pdf',filename='rudin.pdf',content_disposition_type='inline')
@app.post('/api/ask')
async def ask(body:Ask,s=Depends(db)):
    try: return await Agent(s).ask(body.question)
    except Exception as exc:
        # Do not reflect provider responses/credentials to the browser.
        raise HTTPException(502,'模型服务请求失败，请检查 .env 配置和提供商状态。错误类型：'+type(exc).__name__)
@app.get('/api/proposals')
def pending(s=Depends(db)): return proposals(s)
@app.post('/api/extract/{id}')
async def extract(id:str,s=Depends(db)):
    if not OpenAICompatibleChat().configured: raise HTTPException(409,'请先填写模型配置')
    try: return await enrich(s,id)
    except KeyError: raise
    except Exception as exc: raise HTTPException(502,'抽取未写入：'+type(exc).__name__)
@app.post('/api/review/{id}')
def approve(id:str,body:Review,s=Depends(db)): return review(s,id,body.approve)
app.mount('/static',StaticFiles(directory=ROOT/'web'),name='static')
@app.get('/')
def home(): return FileResponse(ROOT/'web/index.html')
