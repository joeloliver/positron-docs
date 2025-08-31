from typing import Optional, List
from datetime import datetime
from sqlmodel import Field, SQLModel, Relationship
from pydantic import BaseModel

# Database Models
class Document(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    filename: str
    content_type: str
    source_url: Optional[str] = None
    upload_date: datetime = Field(default_factory=datetime.utcnow)
    num_chunks: int = 0
    doc_metadata: Optional[str] = None  # JSON string
    
    # Relationship
    chats: List["ChatMessage"] = Relationship(back_populates="document")

class ChatSession(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    title: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Relationship
    messages: List["ChatMessage"] = Relationship(back_populates="session")

class ChatMessage(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    session_id: int = Field(foreign_key="chatsession.id")
    role: str  # "user" or "assistant"
    content: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    document_id: Optional[int] = Field(default=None, foreign_key="document.id")
    
    # Relationships
    session: ChatSession = Relationship(back_populates="messages")
    document: Optional[Document] = Relationship(back_populates="chats")

# API Models
class DocumentUploadResponse(BaseModel):
    id: int
    filename: str
    num_chunks: int
    message: str

class URLIngestRequest(BaseModel):
    url: str
    extract_pdfs: bool = False

class ChatRequest(BaseModel):
    message: str
    session_id: Optional[int] = None
    use_context: bool = True
    top_k: int = 5

class ChatResponse(BaseModel):
    response: str
    session_id: int
    sources: List[dict] = []
    
class SearchRequest(BaseModel):
    query: str
    top_k: int = 5
    
class SearchResult(BaseModel):
    content: str
    metadata: dict
    score: float