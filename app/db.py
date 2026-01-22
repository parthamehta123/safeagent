from sqlalchemy import create_engine, Column, String, JSON, Float, DateTime, Text
from sqlalchemy.orm import declarative_base, sessionmaker
from datetime import datetime
from uuid import uuid4

from app.config import settings

# -------------------------
# Database setup
# -------------------------

engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,
    future=True,
)

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
)

Base = declarative_base()


# -------------------------
# Models
# -------------------------


class AgentSession(Base):
    """
    One row per SafeAgent execution.
    This is your enterprise audit trail.
    """

    __tablename__ = "agent_sessions"

    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    created_at = Column(DateTime, default=datetime.utcnow)

    repo_url = Column(String, nullable=False)
    prompt = Column(String, nullable=False)

    files_changed = Column(JSON)
    plan = Column(JSON)
    result = Column(JSON)
    status = Column(String)
    duration_sec = Column(Float)

    error = Column(String, nullable=True)

    diff = Column(Text, nullable=True)
    trace = Column(JSON, nullable=True)


# -------------------------
# Helpers
# -------------------------


def init_db():
    """
    Call once on app startup to create tables.
    """
    Base.metadata.create_all(bind=engine)


def get_db():
    """
    Dependency for FastAPI routes.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
