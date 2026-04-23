import os
import logging
from pathlib import Path
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, declarative_base

# Load environment variables from .env
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

logger = logging.getLogger("finance_backend")


def _normalize_db_url(url: str) -> str:
    if not url:
        return ""
    if url.startswith("postgres://"):
        return url.replace("postgres://", "postgresql://", 1)
    return url


def _sqlite_fallback_url() -> str:
    return f"sqlite:///{(Path(__file__).resolve().parent.parent / 'backend_local.db').as_posix()}"


def _create_engine(primary_url: str):
    normalized = _normalize_db_url(primary_url)
    if normalized:
        try:
            if normalized.startswith("sqlite"):
                eng = create_engine(
                    normalized,
                    echo=False,
                    connect_args={"check_same_thread": False},
                )
            else:
                eng = create_engine(
                    normalized,
                    echo=False,
                    pool_size=3,
                    max_overflow=5,
                    pool_pre_ping=True,
                    connect_args={"connect_timeout": 5},
                )
            with eng.connect() as conn:
                conn.execute(text("SELECT 1"))
            return eng
        except Exception:
            logger.info("Primary database unreachable. Using local SQLite.")

    return create_engine(
        _sqlite_fallback_url(),
        echo=False,
        connect_args={"check_same_thread": False},
    )


engine = _create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for all ORM models
Base = declarative_base()


def get_db():
    """FastAPI dependency that provides a DB session per request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
