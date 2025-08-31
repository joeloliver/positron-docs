#!/usr/bin/env python3
"""
Test script to verify the Document RAG Interface setup
"""

import os
import sys
from pathlib import Path

def test_imports():
    """Test that all required modules can be imported"""
    try:
        print("Testing imports...")
        
        # Test backend modules
        from backend.config import settings
        print("✓ Config import OK")
        
        from backend.models import Document, ChatSession, ChatMessage
        print("✓ Models import OK")
        
        from backend.embeddings import get_embedding_provider
        print("✓ Embeddings import OK")
        
        from backend.vector_store import VectorStore
        print("✓ Vector store import OK")
        
        from backend.document_processor import DocumentProcessor
        print("✓ Document processor import OK")
        
        from backend.llm import ChatEngine
        print("✓ LLM import OK")
        
        from backend.database import init_db, get_session
        print("✓ Database import OK")
        
        # Test main app
        import app
        print("✓ Main app import OK")
        
        return True
    except ImportError as e:
        print(f"✗ Import error: {e}")
        return False

def test_config():
    """Test configuration"""
    try:
        from backend.config import settings
        print(f"✓ Embedding provider: {settings.embedding_provider}")
        print(f"✓ LLM provider: {settings.llm_provider}")
        print(f"✓ Database URL: {settings.database_url}")
        print(f"✓ Chroma persist dir: {settings.chroma_persist_dir}")
        return True
    except Exception as e:
        print(f"✗ Config error: {e}")
        return False

def test_directories():
    """Test that required directories exist"""
    try:
        from backend.config import settings
        
        dirs = [
            settings.upload_dir,
            settings.chroma_persist_dir,
            "data"
        ]
        
        for dir_path in dirs:
            if Path(dir_path).exists():
                print(f"✓ Directory exists: {dir_path}")
            else:
                print(f"✗ Directory missing: {dir_path}")
                return False
        return True
    except Exception as e:
        print(f"✗ Directory error: {e}")
        return False

def main():
    print("=== Document RAG Interface Setup Test ===\n")
    
    # Test imports
    if not test_imports():
        print("❌ Import test failed")
        return 1
    
    print()
    
    # Test config
    if not test_config():
        print("❌ Config test failed")
        return 1
    
    print()
    
    # Test directories
    if not test_directories():
        print("❌ Directory test failed")
        return 1
    
    print("\n🎉 All tests passed! The system is ready to run.")
    print("\nNext steps:")
    print("1. Copy .env.example to .env and configure as needed")
    print("2. If using Ollama: ollama pull nomic-embed-text && ollama pull llama3.2")
    print("3. Start backend: uvicorn app:app --reload")
    print("4. Start frontend: cd frontend && npm install && npm run dev")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())