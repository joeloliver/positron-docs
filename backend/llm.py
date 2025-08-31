from typing import List, Dict, Any, Optional
import httpx
from openai import OpenAI
from .config import settings
import logging
import json

logger = logging.getLogger(__name__)

class LLMProvider:
    def generate(self, prompt: str, context: Optional[str] = None) -> str:
        raise NotImplementedError
    
    def chat(self, messages: List[Dict[str, str]]) -> str:
        raise NotImplementedError

class OllamaLLM(LLMProvider):
    def __init__(self):
        self.base_url = settings.ollama_base_url
        self.model = settings.ollama_chat_model
    
    def generate(self, prompt: str, context: Optional[str] = None) -> str:
        try:
            full_prompt = prompt
            if context:
                full_prompt = f"Context:\n{context}\n\nQuestion: {prompt}\n\nAnswer:"
            
            with httpx.Client() as client:
                response = client.post(
                    f"{self.base_url}/api/generate",
                    json={
                        "model": self.model,
                        "prompt": full_prompt,
                        "stream": False
                    },
                    timeout=60.0
                )
                response.raise_for_status()
                return response.json()["response"]
        except Exception as e:
            logger.error(f"Ollama generation error: {e}")
            raise
    
    def chat(self, messages: List[Dict[str, str]]) -> str:
        try:
            with httpx.Client() as client:
                response = client.post(
                    f"{self.base_url}/api/chat",
                    json={
                        "model": self.model,
                        "messages": messages,
                        "stream": False
                    },
                    timeout=60.0
                )
                response.raise_for_status()
                return response.json()["message"]["content"]
        except Exception as e:
            logger.error(f"Ollama chat error: {e}")
            raise

class OpenAILLM(LLMProvider):
    def __init__(self):
        if not settings.openai_api_key:
            raise ValueError("OpenAI API key not configured")
        self.client = OpenAI(api_key=settings.openai_api_key)
        self.model = settings.openai_chat_model
    
    def generate(self, prompt: str, context: Optional[str] = None) -> str:
        try:
            messages = []
            if context:
                messages.append({
                    "role": "system",
                    "content": f"Use the following context to answer questions:\n{context}"
                })
            messages.append({"role": "user", "content": prompt})
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.7,
                max_tokens=1000
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"OpenAI generation error: {e}")
            raise
    
    def chat(self, messages: List[Dict[str, str]]) -> str:
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.7,
                max_tokens=1000
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"OpenAI chat error: {e}")
            raise

def get_llm_provider() -> LLMProvider:
    if settings.llm_provider.lower() == "openai":
        return OpenAILLM()
    else:
        return OllamaLLM()

class ChatEngine:
    def __init__(self, vector_store):
        self.llm = get_llm_provider()
        self.vector_store = vector_store
    
    def chat_with_context(
        self, 
        message: str, 
        use_context: bool = True,
        top_k: int = 5
    ) -> Dict[str, Any]:
        """Chat with optional RAG context"""
        
        sources = []
        context = None
        
        if use_context:
            # Search for relevant documents
            search_results = self.vector_store.search(message, top_k=top_k)
            
            if search_results:
                # Build context
                context_parts = []
                for i, result in enumerate(search_results):
                    context_parts.append(f"[{i+1}] {result['content']}")
                    sources.append({
                        "content": result["content"][:200] + "...",
                        "metadata": result["metadata"],
                        "score": result["score"]
                    })
                
                context = "\n\n".join(context_parts)
        
        # Generate response
        response = self.llm.generate(message, context=context)
        
        return {
            "response": response,
            "sources": sources
        }