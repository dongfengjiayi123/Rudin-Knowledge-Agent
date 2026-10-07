"""Optional Agent → real MCP stdio transport (same shared SQLite file)."""
import json
import os
import sys
from contextlib import AsyncExitStack
from mcp import ClientSession,StdioServerParameters
from mcp.client.stdio import stdio_client
from .config import ROOT
from .tools import PARAMS,dispatch

class ToolRuntime:
    def __init__(self,tools):
        self.tools=tools; self.stack=AsyncExitStack(); self.session=None
    async def __aenter__(self):
        if os.getenv('AGENT_TOOL_TRANSPORT','local')=='mcp':
            try:
                env=dict(os.environ,RUDIN_DB=self.tools.store.db_path,PYTHONPATH=str(ROOT))
                params=StdioServerParameters(command=sys.executable,args=['-m','rudin_agent.mcp_server'],cwd=str(ROOT),env=env)
                read,write=await self.stack.enter_async_context(stdio_client(params))
                self.session=await self.stack.enter_async_context(ClientSession(read,write))
                await self.session.initialize()
            except BaseException:
                await self.stack.aclose(); raise
        return self
    async def __aexit__(self,*args): await self.stack.aclose()
    async def call(self,name,args):
        if not self.session: return await dispatch(self.tools,name,args)
        if name not in PARAMS or not isinstance(args,dict): raise ValueError('Unknown tool or invalid arguments')
        result=await self.session.call_tool(name,args)
        if result.isError: raise ValueError('MCP tool returned an error')
        texts=[c.text for c in result.content if c.type=='text']
        return json.loads(texts[0]) if len(texts)==1 else [json.loads(t) for t in texts]
