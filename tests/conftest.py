"""Pytest configuration and fixtures."""
import pytest
import os
import tempfile
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from db import Base, OCRJob
from app import app as flask_app


@pytest.fixture(scope="session")
def test_db():
    """Create a test database for the session."""
    # Create a temporary database file
    db_fd, db_path = tempfile.mkstemp()
    database_url = f"sqlite:///{db_path}"

    # Create engine and tables
    engine = create_engine(database_url)
    Base.metadata.create_all(bind=engine)

    TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    yield TestSessionLocal

    # Cleanup
    os.close(db_fd)
    os.unlink(db_path)


@pytest.fixture
def db_session(test_db):
    """Create a new database session for a test."""
    session = test_db()
    yield session
    session.rollback()
    session.close()


@pytest.fixture
def app():
    """Create application for testing."""
    flask_app.config.update({
        "TESTING": True,
        "WTF_CSRF_ENABLED": False,
    })

    yield flask_app


@pytest.fixture
def client(app):
    """Create a test client."""
    return app.test_client()


@pytest.fixture
def runner(app):
    """Create a test CLI runner."""
    return app.test_cli_runner()
