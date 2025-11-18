import os
from typing import Any
from sqlalchemy import (
    Float,
    create_engine,
    Column,
    String,
    Integer,
    Text,
    DateTime,
    Index
)
from sqlalchemy.orm import declarative_base, sessionmaker
from settings import DATABASE_URL

# Create engine with connection pooling configuration
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,  # Verify connections before using them
    pool_size=10,        # Number of connections to maintain
    max_overflow=20,     # Maximum overflow connections
    pool_recycle=3600    # Recycle connections after 1 hour
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

Base = declarative_base()

class OCRJob(Base):
    __tablename__ = "ocr_jobs"

    id = Column(String, primary_key=True)
    filename = Column(String, nullable=False)
    status = Column(String, nullable=False, index=True)
    method = Column(String, nullable=True)
    result_text = Column(Text, nullable=True)
    duration_ms = Column(Integer, nullable=True)
    created_at = Column(DateTime, nullable=False, index=True)
    error_message = Column(String, nullable=True)
    file_hash = Column(String(64), nullable=True, index=True, unique=True)
    file_size_kb = Column(Float, nullable=True)
    page_count = Column(Integer, nullable=True)

    __table_args__ = (
        Index('idx_status_created_at', 'status', 'created_at'),
    )

def init_db():
    Base.metadata.create_all(bind=engine)
