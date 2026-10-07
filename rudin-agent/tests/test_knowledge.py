import asyncio
import json
import pytest
from rudin_agent.store import Store
from rudin_agent.config import ROOT
from rudin_agent.agent import Agent
from rudin_agent.extract import enrich,proposals,review
from rudin_agent.tools import KnowledgeTools,dispatch

@pytest.fixture
def store():
    s=Store(':memory:').initialize()
    yield s
    s.close()

def test_all_chapters_and_source_provenance(store):
    ns=store.nodes()
    assert {n['chapter'] for n in ns}==set(range(1,12))
    assert store.stats()['pages']==330
    for n in ns:
        text=store.page(n['source']['pdf_page'])['text']
        assert n['ref'] in text
        assert 'EXERCISES' not in n.get('raw','')
    assert store.node('2.32')['source']['printed_page']==33

def test_definition_points_to_related_theorems(store):
    point=KnowledgeTools(store).get_knowledge_point('2.32')
    assert any(e['node']['id']=='4.19' and e['relation']=='uses_definition' for e in point['incoming'])
    assert store.node('2.18.b')['kind']=='definition'
    assert store.path('4.15','2.32')
    assert not store.path('2.32','4.15')
    graph=store.graph('2.32',1)
    ids={n['id'] for n in graph['nodes']}
    assert all(e['source'] in ids and e['target'] in ids for e in graph['edges'])

def test_chinese_and_number_search(store):
    assert store.search('紧致')[0]['status']=='reviewed'
    assert store.search('2.32')[0]['id']=='2.32'
    assert any(n['id']=='7.7' for n in store.search('uniform convergence'))

def test_reference_is_not_a_dependency(store):
    ref=next(e for e in store.edges() if e['relation']=='references')
    assert ref['status']=='indexed'
    assert ref['relation'] not in {'uses_definition','depends_on'}

def test_tool_input_validation(store):
    with pytest.raises(ValueError): asyncio.run(dispatch(KnowledgeTools(store),'read_source',{'pdf_page':-1}))
    with pytest.raises(ValueError): asyncio.run(dispatch(KnowledgeTools(store),'unknown',{}))
    with pytest.raises(KeyError): store.graph('nonexistent')

class ScriptedProvider:
    configured=True
    def __init__(self,replies): self.replies=iter(replies)
    async def complete(self,messages,tools=None): return next(self.replies)

def test_agent_really_calls_tools_and_checks_citations(store):
    provider=ScriptedProvider([
        {'content':None,'tool_calls':[{'id':'t1','type':'function','function':{'name':'get_knowledge_point','arguments':'{"id":"2.32"}'}}]},
        {'content':'紧集的每个开覆盖有有限子覆盖 [2.32]。这个性质与 [99.99] 有关。'}])
    result=asyncio.run(Agent(store,provider).ask('紧致'))
    assert result['trace'][0]['tool']=='get_knowledge_point'
    assert result['unverified_citations']==['99.99']
    assert any(c['id']=='2.32' for c in result['citations'])

def test_no_key_local_mode(store,monkeypatch):
    monkeypatch.delenv('LLM_API_KEY',raising=False);monkeypatch.delenv('LLM_MODEL',raising=False)
    result=asyncio.run(Agent(store).ask('一致连续'))
    assert result['mode']=='local' and result['citations']

def test_extraction_and_human_review_isolated(store):
    original=store.node('2.34')
    proposal={'title':'测试候选','statement':'紧集是闭集。','intuition':'测试','aliases':['测试'],'edges':[{'target':'2.32','relation':'uses_definition','evidence':'Compact subsets of metric spaces are closed.'}]}
    asyncio.run(enrich(store,'2.34',ScriptedProvider([{'content':json.dumps(proposal)}])))
    assert store.node('2.34')==original
    assert proposals(store)[0]['node']['status']=='pending'
    review(store,'2.34',True)
    assert not proposals(store)
    assert store.node('2.34')['title']=='测试候选'

def test_invalid_extraction_is_not_written(store):
    payload={'title':'候选','statement':'x','intuition':'x','edges':[{'target':'99.99','relation':'depends_on','evidence':'made up'}]}
    with pytest.raises(ValueError): asyncio.run(enrich(store,'2.34',ScriptedProvider([{'content':json.dumps(payload)}])))
    assert not proposals(store)

def test_vectors_dimension_and_model(store):
    store.set_vector('2.32','test',[1,0]);store.set_vector('4.5','test',[0,1])
    assert store.vector_search([1,0],'test')[0]['id']=='2.32'
    assert not store.vector_search([1,0,0],'test')
    assert not store.vector_search([1,0],'other')
    node=store.node('2.32'); node['statement']+=' 更新'
    store.put_node(node)
    assert all(n['id']!='2.32' for n in store.vector_search([1,0],'test'))

