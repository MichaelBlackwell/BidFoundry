"""Document management service."""

import uuid
from datetime import datetime
from typing import Literal, Optional

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from server.models.database import Document
from server.models.schemas import DocumentDuplicateRequest, DocumentStatusUpdate


class DocumentsService:
    """Service for managing generated documents."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_all(
        self,
        limit: int = 20,
        offset: int = 0,
        status: Optional[str] = None,
        doc_type: Optional[str] = None,
        search: Optional[str] = None,
        sort_by: str = "createdAt",
        sort_order: Literal["asc", "desc"] = "desc",
    ) -> tuple[list[Document], int]:
        """
        Get all documents with filtering, pagination, and sorting.

        Args:
            limit: Maximum number of results
            offset: Pagination offset
            status: Filter by status (draft, approved, rejected)
            doc_type: Filter by document type
            search: Search in title
            sort_by: Field to sort by (createdAt, updatedAt, title, confidence)
            sort_order: Sort order (asc, desc)

        Returns:
            Tuple of (documents list, total count)
        """
        # Build base query
        base_query = select(Document)

        # Apply filters
        if status:
            base_query = base_query.where(Document.status == status)
        if doc_type:
            base_query = base_query.where(Document.type == doc_type)
        if search:
            base_query = base_query.where(
                or_(
                    Document.title.ilike(f"%{search}%"),
                )
            )

        # Get total count with filters applied
        count_stmt = select(func.count()).select_from(base_query.subquery())
        total_result = await self.db.execute(count_stmt)
        total = total_result.scalar() or 0

        # Map sort_by parameter to column
        sort_column_map = {
            "createdAt": Document.created_at,
            "updatedAt": Document.updated_at,
            "title": Document.title,
            "confidence": Document.confidence,
        }
        sort_column = sort_column_map.get(sort_by, Document.created_at)

        # Apply sorting
        if sort_order == "asc":
            base_query = base_query.order_by(sort_column.asc())
        else:
            base_query = base_query.order_by(sort_column.desc())

        # Apply pagination
        base_query = base_query.offset(offset).limit(limit)

        result = await self.db.execute(base_query)
        documents = list(result.scalars().all())

        return documents, total

    async def get_by_id(self, document_id: str) -> Optional[Document]:
        """Get a document by ID."""
        stmt = select(Document).where(Document.id == document_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def delete(self, document_id: str) -> bool:
        """
        Delete a document.

        Returns:
            True if deleted, False if not found
        """
        document = await self.get_by_id(document_id)
        if not document:
            return False

        await self.db.delete(document)
        await self.db.flush()
        return True

    async def duplicate(
        self, document_id: str, request: DocumentDuplicateRequest
    ) -> Optional[Document]:
        """
        Duplicate a document.

        Args:
            document_id: ID of document to duplicate
            request: Duplicate request with optional new title

        Returns:
            New duplicated document or None if source not found
        """
        source = await self.get_by_id(document_id)
        if not source:
            return None

        # Create new document with copied data
        new_title = request.new_title or f"{source.title} (Copy)"
        new_document = Document(
            id=str(uuid.uuid4()),
            type=source.type,
            title=new_title,
            status="draft",  # Reset status to draft
            confidence=source.confidence,
            company_profile_id=source.company_profile_id,
            content=source.content,
            confidence_report=source.confidence_report,
            red_team_report=source.red_team_report,
            debate_log=source.debate_log,
            metrics=source.metrics,
            generation_config=source.generation_config,
            requires_human_review=False,  # Reset review status
            review_notes=None,
            reviewed_at=None,
        )

        self.db.add(new_document)
        await self.db.flush()
        await self.db.refresh(new_document)
        return new_document

    async def approve(
        self, document_id: str, request: DocumentStatusUpdate
    ) -> Optional[Document]:
        """
        Approve a document after review.

        Args:
            document_id: Document to approve
            request: Status update with optional review notes

        Returns:
            Updated document or None if not found
        """
        document = await self.get_by_id(document_id)
        if not document:
            return None

        document.status = "approved"
        document.review_notes = request.review_notes
        document.reviewed_at = datetime.utcnow()
        document.requires_human_review = False

        await self.db.flush()
        await self.db.refresh(document)
        return document

    async def reject(
        self, document_id: str, request: DocumentStatusUpdate
    ) -> Optional[Document]:
        """
        Reject a document after review.

        Args:
            document_id: Document to reject
            request: Status update with optional review notes

        Returns:
            Updated document or None if not found
        """
        document = await self.get_by_id(document_id)
        if not document:
            return None

        document.status = "rejected"
        document.review_notes = request.review_notes
        document.reviewed_at = datetime.utcnow()
        document.requires_human_review = False

        await self.db.flush()
        await self.db.refresh(document)
        return document
