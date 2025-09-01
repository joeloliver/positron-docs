import os
from pathlib import Path
from typing import Optional
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Embedding Provider
    embedding_provider: str = "ollama"
    
    # Ollama Settings
    ollama_base_url: str = "http://localhost:11434"  # Default/fallback URL
    ollama_embedding_url: str = "http://localhost:11434"  # Embedding model URL
    ollama_chat_url: str = "http://localhost:11434"  # Chat model URL
    ollama_embedding_model: str = "nomic-embed-text"
    ollama_chat_model: str = "llama3.2"
    
    # OpenAI Settings
    openai_api_key: Optional[str] = None
    openai_embedding_model: str = "text-embedding-3-small"
    openai_chat_model: str = "gpt-4o-mini"
    
    # LLM Provider
    llm_provider: str = "ollama"
    
    # Database
    database_url: str = "sqlite:///./data/app.db"
    
    # Chroma Settings
    chroma_persist_dir: str = "./data/chroma_db"
    
    # Upload Settings
    upload_dir: str = "./uploads"
    max_file_size: int = 10485760  # 10MB
    
    # App Settings
    app_name: str = "Positron Docs"
    app_version: str = "1.0.0"
    debug: bool = True
    
    class Config:
        env_file = ".env"
        case_sensitive = False

settings = Settings()

# Create necessary directories
Path(settings.upload_dir).mkdir(parents=True, exist_ok=True)
Path(settings.chroma_persist_dir).mkdir(parents=True, exist_ok=True)
Path("./data").mkdir(parents=True, exist_ok=True)