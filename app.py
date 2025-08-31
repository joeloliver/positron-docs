from fastapi import FastAPI, UploadFile, File, HTTPException, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlmodel import Session, select
from typing import List, Optional
import shutil
from pathlib import Path
import json
import logging
from datetime import datetime
import tempfile
import httpx

from backend.config import settings
from backend.database import init_db, get_session
from backend.models import (
    Document, ChatSession, ChatMessage,
    DocumentUploadResponse, URLIngestRequest,
    ChatRequest, ChatResponse, SearchRequest, SearchResult
)
from backend.vector_store import VectorStore
from backend.document_processor import DocumentProcessor
from backend.llm import ChatEngine

# Configure logging
logging.basicConfig(
    level=logging.INFO if not settings.debug else logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    debug=settings.debug
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize components
vector_store = VectorStore()
doc_processor = DocumentProcessor()
chat_engine = ChatEngine(vector_store)

@app.on_event("startup")
async def startup_event():
    init_db()
    logger.info(f"{settings.app_name} v{settings.app_version} started")

@app.get("/")
async def root():
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "status": "running"
    }

@app.post("/api/upload", response_model=DocumentUploadResponse)
async def upload_document(
    file: UploadFile = File(...),
    session: Session = Depends(get_session),
    background_tasks: BackgroundTasks = BackgroundTasks()
):
    """Upload and process a document"""
    
    # Validate file size
    if file.size > settings.max_file_size:
        raise HTTPException(400, f"File too large. Max size: {settings.max_file_size} bytes")
    
    # Validate file type
    if not file.filename.lower().endswith(('.pdf', '.txt', '.md')):
        raise HTTPException(400, "Unsupported file type. Only PDF, TXT, and MD files are supported")
    
    # Save file
    file_path = Path(settings.upload_dir) / file.filename
    with open(file_path, "wb") as f:
        shutil.copyfileobj(file.file, f)
    
    # Create document record
    doc = Document(
        filename=file.filename,
        content_type=file.content_type or "application/octet-stream"
    )
    session.add(doc)
    session.commit()
    session.refresh(doc)
    
    # Process document
    try:
        if file.filename.lower().endswith('.pdf'):
            chunks, metadatas = doc_processor.process_pdf(str(file_path))
        else:
            with open(file_path, 'r', encoding='utf-8') as f:
                text = f.read()
            chunks, metadatas = doc_processor.process_text(text, file.filename)
        
        # Add to vector store
        num_chunks = vector_store.add_documents(chunks, metadatas, doc.id)
        
        # Update document record
        doc.num_chunks = num_chunks
        doc.doc_metadata = json.dumps({"chunks": num_chunks})
        session.commit()
        
        return DocumentUploadResponse(
            id=doc.id,
            filename=doc.filename,
            num_chunks=num_chunks,
            message=f"Successfully processed {num_chunks} chunks"
        )
    except Exception as e:
        logger.error(f"Error processing document: {e}")
        session.delete(doc)
        session.commit()
        raise HTTPException(500, f"Error processing document: {str(e)}")

@app.post("/api/ingest_url")
async def ingest_url(
    request: URLIngestRequest,
    session: Session = Depends(get_session)
):
    """Ingest content from URL"""
    
    try:
        # Process main URL
        chunks, metadatas = doc_processor.process_url(request.url)
        
        # Create document record
        doc = Document(
            filename=request.url,
            content_type="text/html",
            source_url=request.url
        )
        session.add(doc)
        session.commit()
        session.refresh(doc)
        
        # Add to vector store
        num_chunks = vector_store.add_documents(chunks, metadatas, doc.id)
        
        # Update document
        doc.num_chunks = num_chunks
        session.commit()
        
        pdf_results = []
        
        # Extract and process PDFs if requested
        if request.extract_pdfs:
            pdf_links = doc_processor.extract_pdf_links(request.url)
            
            for pdf_url in pdf_links[:5]:  # Limit to 5 PDFs
                try:
                    # Download PDF
                    with httpx.Client() as client:
                        response = client.get(pdf_url, follow_redirects=True)
                        response.raise_for_status()
                    
                    # Save to temp file
                    with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp:
                        tmp.write(response.content)
                        tmp_path = tmp.name
                    
                    # Process PDF
                    pdf_chunks, pdf_metadatas = doc_processor.process_pdf(tmp_path)
                    
                    # Create document record
                    pdf_doc = Document(
                        filename=pdf_url.split('/')[-1],
                        content_type="application/pdf",
                        source_url=pdf_url
                    )
                    session.add(pdf_doc)
                    session.commit()
                    session.refresh(pdf_doc)
                    
                    # Add to vector store
                    pdf_num_chunks = vector_store.add_documents(
                        pdf_chunks, pdf_metadatas, pdf_doc.id
                    )
                    
                    pdf_doc.num_chunks = pdf_num_chunks
                    session.commit()
                    
                    pdf_results.append({
                        "url": pdf_url,
                        "chunks": pdf_num_chunks
                    })
                    
                    # Clean up temp file
                    Path(tmp_path).unlink()
                    
                except Exception as e:
                    logger.error(f"Error processing PDF {pdf_url}: {e}")
        
        return {
            "main_url": {
                "url": request.url,
                "chunks": num_chunks
            },
            "pdfs": pdf_results
        }
    except Exception as e:
        logger.error(f"Error ingesting URL: {e}")
        raise HTTPException(500, f"Error ingesting URL: {str(e)}")

@app.post("/api/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    session: Session = Depends(get_session)
):
    """Chat with documents"""
    
    # Get or create session
    if request.session_id:
        chat_session = session.get(ChatSession, request.session_id)
        if not chat_session:
            raise HTTPException(404, "Chat session not found")
    else:
        chat_session = ChatSession(title=request.message[:50])
        session.add(chat_session)
        session.commit()
        session.refresh(chat_session)
    
    # Save user message
    user_msg = ChatMessage(
        session_id=chat_session.id,
        role="user",
        content=request.message
    )
    session.add(user_msg)
    session.commit()
    
    # Generate response
    result = chat_engine.chat_with_context(
        request.message,
        use_context=request.use_context,
        top_k=request.top_k
    )
    
    # Save assistant message
    assistant_msg = ChatMessage(
        session_id=chat_session.id,
        role="assistant",
        content=result["response"]
    )
    session.add(assistant_msg)
    
    # Update session timestamp
    chat_session.updated_at = datetime.utcnow()
    session.commit()
    
    return ChatResponse(
        response=result["response"],
        session_id=chat_session.id,
        sources=result["sources"]
    )

@app.get("/api/sessions")
async def get_sessions(session: Session = Depends(get_session)):
    """Get all chat sessions"""
    sessions = session.exec(
        select(ChatSession).order_by(ChatSession.updated_at.desc())
    ).all()
    
    return [
        {
            "id": s.id,
            "title": s.title,
            "created_at": s.created_at.isoformat(),
            "updated_at": s.updated_at.isoformat()
        }
        for s in sessions
    ]

@app.get("/api/sessions/{session_id}/messages")
async def get_session_messages(
    session_id: int,
    session: Session = Depends(get_session)
):
    """Get messages for a chat session"""
    chat_session = session.get(ChatSession, session_id)
    if not chat_session:
        raise HTTPException(404, "Chat session not found")
    
    messages = session.exec(
        select(ChatMessage)
        .where(ChatMessage.session_id == session_id)
        .order_by(ChatMessage.timestamp)
    ).all()
    
    return [
        {
            "id": msg.id,
            "role": msg.role,
            "content": msg.content,
            "timestamp": msg.timestamp.isoformat()
        }
        for msg in messages
    ]

@app.post("/api/search", response_model=List[SearchResult])
async def search_documents(request: SearchRequest):
    """Search documents"""
    results = vector_store.search(request.query, top_k=request.top_k)
    
    return [
        SearchResult(
            content=r["content"],
            metadata=r["metadata"],
            score=r["score"]
        )
        for r in results
    ]

@app.get("/api/documents")
async def get_documents(session: Session = Depends(get_session)):
    """Get all documents"""
    documents = session.exec(
        select(Document).order_by(Document.upload_date.desc())
    ).all()
    
    return [
        {
            "id": doc.id,
            "filename": doc.filename,
            "content_type": doc.content_type,
            "source_url": doc.source_url,
            "upload_date": doc.upload_date.isoformat(),
            "num_chunks": doc.num_chunks
        }
        for doc in documents
    ]

@app.delete("/api/documents/{doc_id}")
async def delete_document(
    doc_id: int,
    session: Session = Depends(get_session)
):
    """Delete a document"""
    doc = session.get(Document, doc_id)
    if not doc:
        raise HTTPException(404, "Document not found")
    
    # Delete from vector store
    vector_store.delete_document(doc_id)
    
    # Delete from database
    session.delete(doc)
    session.commit()
    
    return {"message": "Document deleted successfully"}

@app.get("/api/stats")
async def get_stats(session: Session = Depends(get_session)):
    """Get system statistics"""
    doc_count = session.exec(select(Document)).all()
    session_count = session.exec(select(ChatSession)).all()
    
    return {
        "documents": len(doc_count),
        "chat_sessions": len(session_count),
        "vector_store": vector_store.get_stats()
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=settings.debug)