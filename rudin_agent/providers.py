"""Provider interfaces. API keys remain on the server, never in browser responses."""
import os
from typing import Protocol
import httpx

class ChatProvider(Protocol):
    async def complete(self,messages:list,tools:list|None=None) -> dict: ...

class EmbeddingProvider(Protocol):
    async def embed(self,texts:list[str]) -> list[list[float]]: ...

class OpenAICompatibleChat:
    def __init__(self):
        self.key=os.getenv('LLM_API_KEY',''); self.model=os.getenv('LLM_MODEL','')
        self.base=os.getenv('LLM_BASE_URL','https://api.openai.com/v1').rstrip('/')
    @property
    def configured(self): return bool(self.key and self.model)
    async def complete(self,messages,tools=None):
        if not self.configured: raise ValueError('请在 .env 填写 LLM_API_KEY 和 LLM_MODEL')
        payload={'model':self.model,'messages':messages}
        if tools: payload.update(tools=tools,tool_choice='auto')
        async with httpx.AsyncClient(timeout=float(os.getenv('LLM_TIMEOUT','90'))) as client:
            r=await client.post(self.base+'/chat/completions',headers={'Authorization':'Bearer '+self.key},json=payload)
            r.raise_for_status()
            return r.json()['choices'][0]['message']

class OpenAICompatibleEmbedding:
    def __init__(self):
        self.key=os.getenv('EMBED_API_KEY',''); self.model=os.getenv('EMBED_MODEL',''); self.base=os.getenv('EMBED_BASE_URL','').rstrip('/')
    @property
    def configured(self): return bool(self.key and self.model and self.base)
    async def embed(self,texts):
        if not self.configured: raise ValueError('Embedding provider is not configured')
        async with httpx.AsyncClient(timeout=90) as client:
            r=await client.post(self.base+'/embeddings',headers={'Authorization':'Bearer '+self.key},json={'model':self.model,'input':texts})
            r.raise_for_status()
            return [row['embedding'] for row in sorted(r.json()['data'],key=lambda x:x['index'])]
