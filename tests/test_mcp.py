import asyncio
import json
import os
import sys
from mcp import ClientSession,StdioServerParameters
from mcp.client.stdio import stdio_client
from rudin_agent.config import ROOT

def test_real_mcp_stdio_protocol(tmp_path):
    async def run():
        env=dict(os.environ,RUDIN_DB=str(tmp_path/'mcp.db'),PYTHONPATH=str(ROOT))
        params=StdioServerParameters(command=sys.executable,args=['-m','rudin_agent.mcp_server'],env=env,cwd=str(ROOT))
        async with stdio_client(params) as (reader,writer):
            async with ClientSession(reader,writer) as session:
                await session.initialize()
                names={t.name for t in (await session.list_tools()).tools}
                assert {'search_knowledge','get_knowledge_point','read_source'}<=names
                result=await session.call_tool('get_knowledge_point',{'id':'2.32'})
                assert not result.isError
                payload=json.loads(result.content[0].text)
                assert payload['node']['title']=='紧致集'
                page=await session.call_tool('read_source',{'pdf_page':45})
                assert not page.isError
                resource=await session.read_resource('rudin://point/2.32')
                assert resource.contents
    asyncio.run(run())

def test_agent_over_real_mcp(tmp_path,monkeypatch):
    from rudin_agent.store import Store
    from rudin_agent.agent import Agent
    class Provider:
        configured=True
        def __init__(self): self.round=0
        async def complete(self,messages,tools=None):
            self.round+=1
            if self.round==1: return {'content':None,'tool_calls':[{'id':'mcp1','type':'function','function':{'name':'find_dependency_path','arguments':'{"start":"4.15","end":"2.32"}'}}]}
            data=json.loads(messages[-1]['content'])
            assert data['path'][0]=='4.15' and data['path'][-1]=='2.32'
            return {'content':'紧致集的连续像仍紧致 [4.14]。'}
    monkeypatch.setenv('AGENT_TOOL_TRANSPORT','mcp')
    s=Store(tmp_path/'agent-mcp.db').initialize()
    try:
        result=asyncio.run(Agent(s,Provider()).ask('4.14'))
        assert result['trace'][0]['ok']
    finally: s.close()
