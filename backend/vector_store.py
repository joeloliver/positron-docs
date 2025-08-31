import chromadb
from chromadb.config import Settings as ChromaSettings
from typing import List, Dict, Any
import uuid
from .config import settings
from .embeddings import get_embedding_provider
import logging

logger = logging.getLogger(__name__)

class VectorStore:
    def __init__(self):
        self.client = chromadb.PersistentClient(
            path=settings.chroma_persist_dir,
            settings=ChromaSettings(anonymized_telemetry=False)
        )
        self.collection_name = "documents"
        self.embedding_provider = get_embedding_provider()
        self._init_collection()
    
    def _init_collection(self):
        try:
            self.collection = self.client.get_collection(self.collection_name)
        except:
            self.collection = self.client.create_collection(
                name=self.collection_name,
                metadata={"hnsw:space": "cosine"}
            )
    
    def add_documents(
        self, 
        texts: List[str], 
        metadatas: List[Dict[str, Any]], 
        doc_id: int
    ) -> int:
        """Add documents to vector store and return number of chunks added"""
        try:
            embeddings = self.embedding_provider.embed_batch(texts)
            ids = [f"{doc_id}_{i}" for i in range(len(texts))]
            
            # Add document_id to metadata
            for metadata in metadatas:
                metadata["document_id"] = doc_id
            
            self.collection.add(
                embeddings=embeddings,
                documents=texts,
                metadatas=metadatas,
                ids=ids
            )
            
            return len(texts)
        except Exception as e:
            logger.error(f"Error adding documents to vector store: {e}")
            raise
    
    def search(
        self, 
        query: str, 
        top_k: int = 5,
        filter_dict: Dict[str, Any] = None
    ) -> List[Dict[str, Any]]:
        """Search for similar documents"""
        try:
            query_embedding = self.embedding_provider.embed_text(query)
            
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=top_k,
                where=filter_dict
            )
            
            # Format results
            formatted_results = []
            if results["documents"] and results["documents"][0]:
                for i in range(len(results["documents"][0])):
                    formatted_results.append({
                        "content": results["documents"][0][i],
                        "metadata": results["metadatas"][0][i] if results["metadatas"] else {},
                        "score": 1 - results["distances"][0][i] if results["distances"] else 0
                    })
            
            return formatted_results
        except Exception as e:
            logger.error(f"Error searching vector store: {e}")
            raise
    
    def delete_document(self, doc_id: int):
        """Delete all chunks for a document"""
        try:
            # Get all IDs for this document
            results = self.collection.get(
                where={"document_id": doc_id}
            )
            
            if results["ids"]:
                self.collection.delete(ids=results["ids"])
        except Exception as e:
            logger.error(f"Error deleting document from vector store: {e}")
            raise
    
    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about the vector store"""
        try:
            count = self.collection.count()
            return {
                "total_chunks": count,
                "collection_name": self.collection_name
            }
        except Exception as e:
            logger.error(f"Error getting vector store stats: {e}")
            raise