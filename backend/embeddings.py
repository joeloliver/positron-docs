from typing import List, Optional
import httpx
from openai import OpenAI
from .config import settings
import logging

logger = logging.getLogger(__name__)

class EmbeddingProvider:
    def embed_text(self, text: str) -> List[float]:
        raise NotImplementedError
    
    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        raise NotImplementedError

class OllamaEmbeddings(EmbeddingProvider):
    def __init__(self):
        self.base_url = settings.ollama_base_url
        self.model = settings.ollama_embedding_model
        
    def embed_text(self, text: str) -> List[float]:
        try:
            with httpx.Client() as client:
                response = client.post(
                    f"{self.base_url}/api/embeddings",
                    json={"model": self.model, "prompt": text},
                    timeout=30.0
                )
                response.raise_for_status()
                return response.json()["embedding"]
        except Exception as e:
            logger.error(f"Ollama embedding error: {e}")
            raise
    
    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        embeddings = []
        for text in texts:
            embeddings.append(self.embed_text(text))
        return embeddings

class OpenAIEmbeddings(EmbeddingProvider):
    def __init__(self):
        if not settings.openai_api_key:
            raise ValueError("OpenAI API key not configured")
        self.client = OpenAI(api_key=settings.openai_api_key)
        self.model = settings.openai_embedding_model
    
    def embed_text(self, text: str) -> List[float]:
        try:
            response = self.client.embeddings.create(
                model=self.model,
                input=text
            )
            return response.data[0].embedding
        except Exception as e:
            logger.error(f"OpenAI embedding error: {e}")
            raise
    
    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        try:
            response = self.client.embeddings.create(
                model=self.model,
                input=texts
            )
            return [item.embedding for item in response.data]
        except Exception as e:
            logger.error(f"OpenAI batch embedding error: {e}")
            raise

def get_embedding_provider() -> EmbeddingProvider:
    if settings.embedding_provider.lower() == "openai":
        return OpenAIEmbeddings()
    else:
        return OllamaEmbeddings()