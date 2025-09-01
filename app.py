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

# Configure logging - Force DEBUG for testing
logging.basicConfig(
    level=logging.DEBUG,  # Always DEBUG for now to troubleshoot
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Reduce noise from verbose libraries
logging.getLogger("httpx").setLevel(logging.INFO)
logging.getLogger("httpcore").setLevel(logging.WARNING)
logging.getLogger("trafilatura").setLevel(logging.WARNING)

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
    
    logger.info(f"=== Starting URL ingestion ===")
    logger.info(f"URL: {request.url}")
    logger.info(f"Extract PDFs: {request.extract_pdfs}")
    
    try:
        # Process main URL
        logger.info(f"Step 1: Processing main URL content")
        chunks, metadatas = doc_processor.process_url(request.url)
        logger.info(f"Main URL processed: {len(chunks)} chunks extracted")
        
        # Create document record
        logger.info(f"Step 2: Creating document record in database")
        doc = Document(
            filename=request.url,
            content_type="text/html",
            source_url=request.url
        )
        session.add(doc)
        session.commit()
        session.refresh(doc)
        logger.info(f"Document record created with ID: {doc.id}")
        
        # Add to vector store
        logger.info(f"Step 3: Adding chunks to vector store")
        num_chunks = vector_store.add_documents(chunks, metadatas, doc.id)
        logger.info(f"Added {num_chunks} chunks to vector store")
        
        # Update document
        doc.num_chunks = num_chunks
        session.commit()
        logger.info(f"Document record updated with chunk count")
        
        pdf_results = []
        
        # Extract and process PDFs if requested
        if request.extract_pdfs:
            logger.info(f"Step 4: PDF extraction requested")
            logger.info(f"About to call extract_pdf_links for {request.url}")
            
            try:
                pdf_links = doc_processor.extract_pdf_links(request.url)
                logger.info(f"extract_pdf_links completed - Found {len(pdf_links)} potential PDF links")
                if pdf_links:
                    logger.info(f"PDF URLs found: {pdf_links}")
            except Exception as e:
                logger.error(f"Failed to extract PDF links: {e}", exc_info=True)
                pdf_links = []
            
            for pdf_url in pdf_links[:3]:  # Limit to 3 PDFs to reduce memory usage
                try:
                    logger.info(f"Attempting to download PDF from: {pdf_url}")
                    
                    # Download PDF with timeout and headers
                    with httpx.Client(timeout=30.0) as client:  # Reduced timeout
                        headers = {
                            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                        }
                        
                        # Stream the response to check size first
                        with client.stream('GET', pdf_url, follow_redirects=True, headers=headers) as response:
                            response.raise_for_status()
                            
                            # Check content type
                            content_type = response.headers.get('content-type', '').lower()
                            content_length = response.headers.get('content-length')
                            logger.info(f"Content-Type for {pdf_url}: {content_type}")
                            logger.info(f"Content-Length for {pdf_url}: {content_length}")
                            
                            # Skip if too large (>20MB)
                            if content_length and int(content_length) > 20_000_000:
                                logger.warning(f"PDF {pdf_url} is too large ({content_length} bytes). Skipping.")
                                continue
                            
                            # Verify it's actually a PDF
                            if 'pdf' not in content_type:
                                logger.warning(f"URL {pdf_url} does not appear to be a PDF. Skipping.")
                                continue
                            
                            # Read content in chunks to manage memory
                            content = b''
                            for chunk in response.iter_bytes(chunk_size=8192):
                                content += chunk
                                # Stop if getting too large during download
                                if len(content) > 20_000_000:
                                    logger.warning(f"PDF {pdf_url} exceeded 20MB during download. Stopping.")
                                    break
                    
                    # Save to temp file
                    with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp:
                        tmp.write(content)
                        tmp_path = tmp.name
                    
                    logger.info(f"Downloaded PDF to temp file: {len(content)} bytes")
                    
                    logger.info(f"Processing PDF: {pdf_url}")
                    
                    # Process PDF
                    pdf_chunks, pdf_metadatas = doc_processor.process_pdf(tmp_path)
                    
                    if not pdf_chunks:
                        logger.warning(f"No content extracted from PDF: {pdf_url}")
                        Path(tmp_path).unlink()
                        continue
                    
                    # Create document record
                    pdf_filename = pdf_url.split('/')[-1] or f"document_{len(pdf_results)}.pdf"
                    pdf_doc = Document(
                        filename=pdf_filename[:255],  # Limit filename length
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
                        "chunks": pdf_num_chunks,
                        "filename": pdf_filename
                    })
                    
                    logger.info(f"Successfully processed PDF {pdf_url}: {pdf_num_chunks} chunks")
                    
                    # Clean up temp file
                    Path(tmp_path).unlink()
                    
                except httpx.TimeoutException:
                    logger.error(f"Timeout downloading PDF {pdf_url}")
                except httpx.HTTPStatusError as e:
                    logger.error(f"HTTP error downloading PDF {pdf_url}: {e.response.status_code}")
                except Exception as e:
                    logger.error(f"Error processing PDF {pdf_url}: {str(e)}", exc_info=True)
                    # Clean up temp file if it exists
                    if 'tmp_path' in locals() and Path(tmp_path).exists():
                        Path(tmp_path).unlink()
        
        logger.info(f"=== URL ingestion completed successfully ===")
        logger.info(f"Main URL chunks: {num_chunks}")
        logger.info(f"PDFs processed: {len(pdf_results)}")
        
        return {
            "main_url": {
                "url": request.url,
                "chunks": num_chunks
            },
            "pdfs": pdf_results
        }
    except httpx.TimeoutException as e:
        logger.error(f"Timeout error during URL ingestion: {e}")
        raise HTTPException(504, f"Request timed out while processing URL")
    except httpx.HTTPStatusError as e:
        logger.error(f"HTTP error during URL ingestion: {e.response.status_code}")
        raise HTTPException(502, f"Failed to fetch URL: HTTP {e.response.status_code}")
    except Exception as e:
        logger.error(f"Unexpected error ingesting URL: {e}", exc_info=True)
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

@app.delete("/api/sessions/{session_id}")
async def delete_session(
    session_id: int,
    session: Session = Depends(get_session)
):
    """Delete a chat session and all its messages"""
    chat_session = session.get(ChatSession, session_id)
    if not chat_session:
        raise HTTPException(404, "Chat session not found")
    
    # Delete all messages in the session (cascade should handle this, but being explicit)
    messages = session.exec(
        select(ChatMessage).where(ChatMessage.session_id == session_id)
    ).all()
    for msg in messages:
        session.delete(msg)
    
    # Delete the session
    session.delete(chat_session)
    session.commit()
    
    return {"message": "Session deleted successfully"}

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