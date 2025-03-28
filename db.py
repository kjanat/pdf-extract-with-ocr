import os
from typing import Any
from sqlalchemy import (
    Float,
    create_engine,
    Column,
    String,
    Integer,
    Text,
    DateTime
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from settings import DATABASE_URL

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(
    autocommit=False, 
    autoflush=False, 
    bind=engine
)
Base = declarative_base()

class OCRJob(Base):
    __tablename__ = "ocr_jobs"

    id = Column(String, primary_key=True) # , index=True
    filename = Column(String, nullable=False)
    status = Column(String, nullable=False)
    method = Column(String, nullable=True)
    result_text = Column(Text, nullable=True)
    duration_ms = Column(Integer, nullable=True)
    created_at = Column(DateTime, nullable=False)
    error_message = Column(String, nullable=True)
    file_hash = Column(String(64), nullable=True) #, index=True, unique=True
    file_size_kb = Column(Float, nullable=True)
    page_count = Column(Integer, nullable=True)

    # def __init__(self, **kwargs: Any) -> None:
    #     for key, value in kwargs.items():
    #         setattr(self, key, value)

def init_db():
    Base.metadata.create_all(bind=engine)
