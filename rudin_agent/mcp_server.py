"""Real MCP SDK server; tools share exactly the same knowledge store as the web app."""
import os
import json
from mcp.server.fastmcp import FastMCP
from .store import Store
from .tools import KnowledgeTools

mcp=FastMCP('Rudin Knowledge',host=os.getenv('MCP_HOST','127.0.0.1'),port=int(os.getenv('MCP_PORT','8001')),json_response=True)

def use(name,**args):
    s=Store().initialize()
    try: return getattr(KnowledgeTools(s),name)(**args)
    finally: s.close()

@mcp.tool()
def search_knowledge(query:str,limit:int=8)->list:
    """Search Rudin definitions and theorems by Chinese/English name or numbered ID."""
    return use('search_knowledge',query=query,limit=limit)
@mcp.tool()
def get_knowledge_point(id:str)->dict:
    """Read DEF/THM statement, prerequisites and theorems involving a definition."""
    return use('get_knowledge_point',id=id)
@mcp.tool()
def get_neighborhood(id:str,depth:int=1)->dict:
    """Read the typed graph. references is NOT a verified proof dependency."""
    return use('get_neighborhood',id=id,depth=depth)
@mcp.tool()
def find_dependency_path(start:str,end:str)->dict:
    """Follow directed edges from dependent theorem to prerequisite."""
    return use('find_dependency_path',start=start,end=end)
@mcp.tool()
def read_source(pdf_page:int)->dict:
    """Read a 1-indexed PDF page, including printed page label when known."""
    return use('read_source',pdf_page=pdf_page)
@mcp.tool()
def search_source(query:str,limit:int=3)->list:
    """Search the entire book's raw text; English terms are recommended."""
    return use('search_source',query=query,limit=limit)
@mcp.resource('rudin://point/{id}')
def point_resource(id:str)->str:
    return json.dumps(use('get_knowledge_point',id=id),ensure_ascii=False)
@mcp.prompt()
def explain_definition(id:str)->str:
    return f'读取 Rudin 知识点 {id}，完整写出定义、涉及该定义的定理及其条件，区分原文引用和证明依赖，并给出书中编号与 PDF 页码。'

if __name__=='__main__':
    import sys
    mcp.run(transport='streamable-http' if '--http' in sys.argv else 'stdio')
