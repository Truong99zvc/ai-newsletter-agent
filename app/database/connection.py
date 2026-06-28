"""
Database connection management.

Provides SQLAlchemy engine and session factory using
centralized Pydantic Settings configuration.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from app.settings import get_settings


def get_database_url() -> str:
    """Get the database URL from application settings."""
    return get_settings().database.url


engine = create_engine(get_database_url(), pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_session() -> Session:
    """Create a new database session."""
    return SessionLocal()


def get_db():
    """
    FastAPI dependency for database sessions.

    Yields a session and ensures it is closed after use.
    Usage in FastAPI routes:
        @router.get("/items")
        def get_items(db: Session = Depends(get_db)):
            ...
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
