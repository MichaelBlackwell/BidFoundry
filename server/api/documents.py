"""Document API endpoints."""

from typing import Literal, Optional

from fastapi import APIRouter, HTTPException, Query, Request, status
from fastapi.responses import Response

from server.dependencies import DbSession
from server.models.schemas import (
    ConfidenceReportSchema,
    DocumentContentSchema,
    DocumentDuplicateRequest,
    DocumentListItemSchema,
    DocumentListResponse,
    DocumentResponse,
    DocumentStatusUpdate,
    ExportRequest,
    GenerationMetricsSchema,
    RedTeamReportSchema,
    ShareLinkAccessRequest,
    ShareLinkCreateRequest,
    ShareLinkListResponse,
    ShareLinkResponse,
)
from server.services.documents import DocumentsService
from server.services.export import ExportService, ShareLinkService

router = APIRouter()


def _build_document_response(document) -> DocumentResponse:
    """Build a full DocumentResponse from a database Document model."""
    # Parse content if available
    content = None
    if document.content:
        # Transform sections from stored format to API schema format
        # Stored format uses "name" field, API schema expects "id" and "title"
        raw_sections = document.content.get("sections", [])
        transformed_sections = []
        for idx, section in enumerate(raw_sections):
            # Use name as title, generate id from index if not present
            section_name = section.get("name", section.get("title", f"Section {idx + 1}"))
            section_id = section.get("id", f"section-{idx}")
            section_content = section.get("content", "")

            # Get confidence from metadata if available
            metadata = section.get("metadata", {})
            confidence = metadata.get("confidence_score", 0.0) * 100  # Convert to percentage
            unresolved = metadata.get("total_critiques", 0) - metadata.get("resolved_critiques", 0)

            transformed_sections.append({
                "id": section_id,
                "title": section_name,
                "content": section_content,
                "confidence": confidence,
                "unresolvedCritiques": max(0, unresolved),
            })

        content = DocumentContentSchema(
            id=document.id,
            sections=transformed_sections,
            overallConfidence=document.content.get("overallConfidence", 0.0),
            updatedAt=document.updated_at,
        )

    # Parse confidence report if available
    confidence = None
    if document.confidence_report:
        confidence = ConfidenceReportSchema(
            overall=document.confidence_report.get("overall", document.confidence),
            sections=document.confidence_report.get("sections", {}),
        )

    # Parse red team report if available
    red_team_report = None
    if document.red_team_report:
        # Handle summary - it can be a string or a dict with statistics
        raw_summary = document.red_team_report.get("summary", "")
        if isinstance(raw_summary, dict):
            # Convert summary dict to a readable string
            total_critiques = raw_summary.get("total_critiques", 0)
            total_rounds = raw_summary.get("total_rounds", 0)
            resolution_rate = raw_summary.get("resolution_rate", 0.0)
            consensus = "Reached" if raw_summary.get("consensus_reached", False) else "Not Reached"
            summary_text = (
                f"Red Team Report: {total_critiques} critiques across {total_rounds} rounds. "
                f"Resolution rate: {resolution_rate:.1f}%. Consensus: {consensus}."
            )
        else:
            summary_text = raw_summary

        red_team_report = RedTeamReportSchema(
            entries=document.red_team_report.get("entries", []),
            summary=summary_text,
        )

    # Parse metrics if available
    metrics = None
    if document.metrics:
        metrics = GenerationMetricsSchema(**document.metrics)

    return DocumentResponse(
        documentId=document.id,
        content=content,
        confidence=confidence,
        redTeamReport=red_team_report,
        debateLog=document.debate_log or [],
        metrics=metrics,
        requiresHumanReview=document.requires_human_review,
    )


@router.get("", response_model=DocumentListResponse)
async def list_documents(
    db: DbSession,
    limit: int = Query(default=20, ge=1, le=100, description="Maximum number of results"),
    offset: int = Query(default=0, ge=0, description="Pagination offset"),
    status: Optional[str] = Query(default=None, description="Filter: draft, approved, rejected"),
    type: Optional[str] = Query(default=None, description="Filter by document type"),
    search: Optional[str] = Query(default=None, description="Search in title"),
    sortBy: str = Query(default="createdAt", description="Sort by: createdAt, updatedAt, title, confidence"),
    sortOrder: Literal["asc", "desc"] = Query(default="desc", description="Sort order: asc, desc"),
) -> DocumentListResponse:
    """List all documents with filtering, pagination, and sorting."""
    service = DocumentsService(db)
    documents, total = await service.get_all(
        limit=limit,
        offset=offset,
        status=status,
        doc_type=type,
        search=search,
        sort_by=sortBy,
        sort_order=sortOrder,
    )

    return DocumentListResponse(
        documents=[DocumentListItemSchema.model_validate(d) for d in documents],
        total=total,
    )


@router.get("/{document_id}", response_model=DocumentResponse)
async def get_document(
    document_id: str,
    db: DbSession,
) -> DocumentResponse:
    """Get a document by ID with full output data."""
    service = DocumentsService(db)
    document = await service.get_by_id(document_id)

    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": "DOCUMENT_NOT_FOUND",
                "message": f"Document not found: {document_id}",
                "details": {"documentId": document_id},
            },
        )

    return _build_document_response(document)


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(
    document_id: str,
    db: DbSession,
) -> None:
    """Delete a document."""
    service = DocumentsService(db)
    deleted = await service.delete(document_id)

    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": "DOCUMENT_NOT_FOUND",
                "message": f"Document not found: {document_id}",
                "details": {"documentId": document_id},
            },
        )


@router.post("/{document_id}/duplicate", response_model=DocumentListItemSchema, status_code=status.HTTP_201_CREATED)
async def duplicate_document(
    document_id: str,
    db: DbSession,
    request: DocumentDuplicateRequest = DocumentDuplicateRequest(),
) -> DocumentListItemSchema:
    """Duplicate a document."""
    service = DocumentsService(db)
    new_document = await service.duplicate(document_id, request)

    if not new_document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": "DOCUMENT_NOT_FOUND",
                "message": f"Document not found: {document_id}",
                "details": {"documentId": document_id},
            },
        )

    return DocumentListItemSchema.model_validate(new_document)


@router.post("/{document_id}/approve", response_model=DocumentListItemSchema)
async def approve_document(
    document_id: str,
    db: DbSession,
    request: DocumentStatusUpdate = DocumentStatusUpdate(),
) -> DocumentListItemSchema:
    """Approve a document after review."""
    service = DocumentsService(db)
    document = await service.approve(document_id, request)

    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": "DOCUMENT_NOT_FOUND",
                "message": f"Document not found: {document_id}",
                "details": {"documentId": document_id},
            },
        )

    return DocumentListItemSchema.model_validate(document)


@router.post("/{document_id}/reject", response_model=DocumentListItemSchema)
async def reject_document(
    document_id: str,
    db: DbSession,
    request: DocumentStatusUpdate = DocumentStatusUpdate(),
) -> DocumentListItemSchema:
    """Reject a document after review."""
    service = DocumentsService(db)
    document = await service.reject(document_id, request)

    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": "DOCUMENT_NOT_FOUND",
                "message": f"Document not found: {document_id}",
                "details": {"documentId": document_id},
            },
        )

    return DocumentListItemSchema.model_validate(document)


# ============================================================================
# Export Endpoints
# ============================================================================


@router.get("/{document_id}/export")
async def export_document(
    document_id: str,
    db: DbSession,
    format: Literal["word", "pdf", "markdown"] = Query(
        default="pdf",
        description="Export format: word, pdf, markdown",
    ),
) -> Response:
    """
    Export a document to the specified format.

    Returns the file as a download.
    """
    # Get the document
    documents_service = DocumentsService(db)
    document = await documents_service.get_by_id(document_id)

    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": "DOCUMENT_NOT_FOUND",
                "message": f"Document not found: {document_id}",
                "details": {"documentId": document_id},
            },
        )

    # Export the document
    export_service = ExportService(db)
    try:
        file_bytes, filename, content_type = await export_service.export_document(
            document, format
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "code": "EXPORT_FAILED",
                "message": f"Failed to export document: {str(e)}",
                "details": {"documentId": document_id, "format": format},
            },
        )

    return Response(
        content=file_bytes,
        media_type=content_type,
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "Content-Length": str(len(file_bytes)),
        },
    )


# ============================================================================
# Share Link Endpoints
# ============================================================================


def _build_share_link_response(
    share_link, request: Request
) -> ShareLinkResponse:
    """Build a ShareLinkResponse from a ShareLink model."""
    # Build the full URL
    base_url = str(request.base_url).rstrip("/")
    share_url = f"{base_url}/api/documents/shared/{share_link.token}"

    return ShareLinkResponse(
        id=share_link.id,
        documentId=share_link.document_id,
        token=share_link.token,
        url=share_url,
        hasPassword=share_link.password_hash is not None,
        expiresAt=share_link.expires_at,
        createdAt=share_link.created_at,
    )


@router.post("/{document_id}/share", response_model=ShareLinkResponse, status_code=status.HTTP_201_CREATED)
async def create_share_link(
    document_id: str,
    request: Request,
    db: DbSession,
    body: ShareLinkCreateRequest = ShareLinkCreateRequest(),
) -> ShareLinkResponse:
    """Create a shareable link for a document."""
    # Verify document exists
    documents_service = DocumentsService(db)
    document = await documents_service.get_by_id(document_id)

    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": "DOCUMENT_NOT_FOUND",
                "message": f"Document not found: {document_id}",
                "details": {"documentId": document_id},
            },
        )

    # Create share link
    share_service = ShareLinkService(db)
    share_link = await share_service.create_share_link(
        document_id=document_id,
        password=body.password,
        expires_in_days=body.expires_in_days,
    )

    return _build_share_link_response(share_link, request)


@router.get("/{document_id}/share", response_model=ShareLinkListResponse)
async def list_share_links(
    document_id: str,
    request: Request,
    db: DbSession,
) -> ShareLinkListResponse:
    """List all share links for a document."""
    # Verify document exists
    documents_service = DocumentsService(db)
    document = await documents_service.get_by_id(document_id)

    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": "DOCUMENT_NOT_FOUND",
                "message": f"Document not found: {document_id}",
                "details": {"documentId": document_id},
            },
        )

    # Get share links
    share_service = ShareLinkService(db)
    share_links = await share_service.get_share_links_for_document(document_id)

    return ShareLinkListResponse(
        shareLinks=[_build_share_link_response(sl, request) for sl in share_links],
        total=len(share_links),
    )


@router.delete("/{document_id}/share/{share_link_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_share_link(
    document_id: str,
    share_link_id: str,
    db: DbSession,
) -> None:
    """Delete a share link."""
    share_service = ShareLinkService(db)
    deleted = await share_service.delete_share_link(share_link_id)

    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": "SHARE_LINK_NOT_FOUND",
                "message": f"Share link not found: {share_link_id}",
                "details": {"shareLinkId": share_link_id},
            },
        )


@router.get("/shared/{token}", response_model=DocumentResponse)
async def get_shared_document(
    token: str,
    db: DbSession,
    password: Optional[str] = Query(None, description="Password if required"),
) -> DocumentResponse:
    """
    Access a shared document via its share link token.

    If the share link is password-protected, provide the password as a query parameter.
    """
    share_service = ShareLinkService(db)
    is_valid, error_message, share_link = await share_service.validate_share_link(
        token, password
    )

    if not is_valid:
        if error_message == "Password required":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={
                    "code": "PASSWORD_REQUIRED",
                    "message": "This share link requires a password",
                    "details": {"requiresPassword": True},
                },
            )
        elif error_message == "Invalid password":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={
                    "code": "INVALID_PASSWORD",
                    "message": "Invalid password",
                    "details": {},
                },
            )
        elif error_message == "Share link has expired":
            raise HTTPException(
                status_code=status.HTTP_410_GONE,
                detail={
                    "code": "SHARE_LINK_EXPIRED",
                    "message": "This share link has expired",
                    "details": {},
                },
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "code": "SHARE_LINK_NOT_FOUND",
                    "message": "Share link not found",
                    "details": {},
                },
            )

    # Get the document
    documents_service = DocumentsService(db)
    document = await documents_service.get_by_id(share_link.document_id)

    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": "DOCUMENT_NOT_FOUND",
                "message": "The shared document no longer exists",
                "details": {},
            },
        )

    return _build_document_response(document)
