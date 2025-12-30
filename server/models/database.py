"""SQLAlchemy database configuration and models."""

import uuid
from datetime import datetime
from typing import AsyncGenerator

from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, String, Text
from sqlalchemy.dialects.sqlite import JSON
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, relationship

from server.config import settings


class Base(DeclarativeBase):
    """Base class for all database models."""

    pass


class CompanyProfile(Base):
    """Company profile model."""

    __tablename__ = "company_profiles"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False)
    description = Column(Text)
    naics_codes = Column(JSON, default=list)
    certifications = Column(JSON, default=list)
    past_performance = Column(JSON, default=list)
    full_profile = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    documents = relationship("Document", back_populates="company_profile")


class Document(Base):
    """Generated document model."""

    __tablename__ = "documents"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    type = Column(String, nullable=False)
    title = Column(String, nullable=False)
    status = Column(String, default="draft")
    confidence = Column(Float, default=0.0)

    company_profile_id = Column(String, ForeignKey("company_profiles.id"))
    company_profile = relationship("CompanyProfile", back_populates="documents")

    content = Column(JSON)
    confidence_report = Column(JSON)
    red_team_report = Column(JSON)
    debate_log = Column(JSON)
    metrics = Column(JSON)
    generation_config = Column(JSON)

    requires_human_review = Column(Boolean, default=False)
    review_notes = Column(Text)
    reviewed_at = Column(DateTime)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class GenerationRequest(Base):
    """Tracks active and completed generation requests."""

    __tablename__ = "generation_requests"

    id = Column(String, primary_key=True)
    document_id = Column(String, ForeignKey("documents.id"))
    status = Column(String, default="queued")

    current_round = Column(String, default="0")
    total_rounds = Column(String)
    current_phase = Column(String)

    started_at = Column(DateTime)
    completed_at = Column(DateTime)

    error_message = Column(Text)
    error_code = Column(String)


class ShareLink(Base):
    """Shareable document links."""

    __tablename__ = "share_links"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    document_id = Column(String, ForeignKey("documents.id"))
    token = Column(String, unique=True)
    password_hash = Column(String)
    expires_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)


# Database engine and session factory
engine = create_async_engine(
    settings.database_url,
    echo=settings.debug,
)

async_session_maker = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def init_db() -> None:
    """Create all database tables."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency that provides a database session."""
    async with async_session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
