from fastapi.testclient import TestClient
from rudin_agent.api import app,db
from rudin_agent.store import Store

def test_http_end_to_end(tmp_path,monkeypatch):
    path=tmp_path/'test.db';s=Store(path).initialize();s.close()
    def connection():
        s=Store(path)
        try: yield s
        finally: s.close()
    app.dependency_overrides[db]=connection
    monkeypatch.delenv('LLM_API_KEY',raising=False)
    try:
        with TestClient(app) as client:
            assert client.get('/').status_code==200
            assert client.get('/static/app.js').status_code==200
            assert client.get('/api/status').json()['reviewed']==52
            assert client.get('/api/concepts/2.32').json()['node']['kind']=='definition'
            assert client.get('/api/concepts?q=一致连续&reviewed=true').json()[0]['id']=='4.18'
            assert client.get('/api/concepts/nonexistent').status_code==404
            assert client.get('/api/graph/2.32?depth=4').status_code==422
            assert client.get('/api/book').headers['content-type']=='application/pdf'
            assert client.post('/api/ask',json={'question':'紧致'}).json()['mode']=='local'
            assert client.post('/api/extract/2.32',json={}).status_code==409
            assert client.post('/api/ask',json={'question':''}).status_code==422
            assert client.post('/api/ask',json={'question':'x'},headers={'origin':'https://example.com'}).status_code==403
    finally: app.dependency_overrides.clear()
