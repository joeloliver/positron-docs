from sqlmodel import create_engine, SQLModel, Session
from .config import settings
import logging

logger = logging.getLogger(__name__)

# Create engine
engine = create_engine(
    settings.database_url,
    connect_args={"check_same_thread": False} if "sqlite" in settings.database_url else {},
    echo=settings.debug
)

def init_db():
    """Initialize database tables"""
    SQLModel.metadata.create_all(engine)
    logger.info("Database initialized")

def get_session():
    """Get database session"""
    with Session(engine) as session:
        yield session