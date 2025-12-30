"""Integration tests for the Documents API endpoints."""

import pytest
import pytest_asyncio
from httpx import AsyncClient

from server.models.database import Document

pytestmark = pytest.mark.asyncio(loop_scope="function")


class TestListDocuments:
    """Tests for GET /api/documents."""

    async def test_list_documents_empty(self, client: AsyncClient):
        """Should return empty list when no documents exist."""
        response = await client.get("/api/documents")
        assert response.status_code == 200
        data = response.json()
        assert data["documents"] == []
        assert data["total"] == 0

    async def test_list_documents_with_data(
        self, client: AsyncClient, db_documents: list[Document]
    ):
        """Should return list of documents."""
        response = await client.get("/api/documents")
        assert response.status_code == 200
        data = response.json()
        assert len(data["documents"]) == 5
        assert data["total"] == 5

        # Check document structure
        doc = data["documents"][0]
        assert "id" in doc
        assert "type" in doc
        assert "title" in doc
        assert "status" in doc
        assert "confidence" in doc
        assert "createdAt" in doc
        assert "updatedAt" in doc

    async def test_list_documents_pagination(
        self, client: AsyncClient, db_documents: list[Document]
    ):
        """Should respect limit and offset parameters."""
        # Test limit
        response = await client.get("/api/documents?limit=2")
        data = response.json()
        assert len(data["documents"]) == 2
        assert data["total"] == 5

        # Test offset
        response = await client.get("/api/documents?limit=2&offset=2")
        data = response.json()
        assert len(data["documents"]) == 2
        assert data["total"] == 5

        # Test offset beyond data
        response = await client.get("/api/documents?limit=10&offset=10")
        data = response.json()
        assert len(data["documents"]) == 0
        assert data["total"] == 5

    async def test_list_documents_filter_by_status(
        self, client: AsyncClient, db_documents: list[Document]
    ):
        """Should filter documents by status."""
        # Filter draft
        response = await client.get("/api/documents?status=draft")
        data = response.json()
        assert data["total"] == 2
        for doc in data["documents"]:
            assert doc["status"] == "draft"

        # Filter approved
        response = await client.get("/api/documents?status=approved")
        data = response.json()
        assert data["total"] == 2
        for doc in data["documents"]:
            assert doc["status"] == "approved"

        # Filter rejected
        response = await client.get("/api/documents?status=rejected")
        data = response.json()
        assert data["total"] == 1
        assert data["documents"][0]["status"] == "rejected"

    async def test_list_documents_filter_by_type(
        self, client: AsyncClient, db_documents: list[Document]
    ):
        """Should filter documents by type."""
        response = await client.get("/api/documents?type=capability-statement")
        data = response.json()
        assert data["total"] == 3
        for doc in data["documents"]:
            assert doc["type"] == "capability-statement"

        response = await client.get("/api/documents?type=proposal")
        data = response.json()
        assert data["total"] == 2
        for doc in data["documents"]:
            assert doc["type"] == "proposal"

    async def test_list_documents_search(
        self, client: AsyncClient, db_documents: list[Document]
    ):
        """Should search documents by title."""
        response = await client.get("/api/documents?search=Document%201")
        data = response.json()
        assert data["total"] == 1
        assert "Document 1" in data["documents"][0]["title"]

        # Case insensitive search
        response = await client.get("/api/documents?search=test")
        data = response.json()
        assert data["total"] == 5

    async def test_list_documents_sorting(
        self, client: AsyncClient, db_documents: list[Document]
    ):
        """Should sort documents by specified field."""
        # Sort by confidence ascending
        response = await client.get("/api/documents?sortBy=confidence&sortOrder=asc")
        data = response.json()
        confidences = [doc["confidence"] for doc in data["documents"]]
        assert confidences == sorted(confidences)

        # Sort by confidence descending
        response = await client.get("/api/documents?sortBy=confidence&sortOrder=desc")
        data = response.json()
        confidences = [doc["confidence"] for doc in data["documents"]]
        assert confidences == sorted(confidences, reverse=True)

        # Sort by title
        response = await client.get("/api/documents?sortBy=title&sortOrder=asc")
        data = response.json()
        titles = [doc["title"] for doc in data["documents"]]
        assert titles == sorted(titles)

    async def test_list_documents_combined_filters(
        self, client: AsyncClient, db_documents: list[Document]
    ):
        """Should handle multiple filters together."""
        response = await client.get(
            "/api/documents?status=draft&type=capability-statement&limit=10"
        )
        data = response.json()
        for doc in data["documents"]:
            assert doc["status"] == "draft"
            assert doc["type"] == "capability-statement"


class TestGetDocument:
    """Tests for GET /api/documents/{id}."""

    async def test_get_document_success(
        self, client: AsyncClient, db_document: Document
    ):
        """Should return full document by ID."""
        response = await client.get(f"/api/documents/{db_document.id}")
        assert response.status_code == 200
        data = response.json()

        assert data["documentId"] == db_document.id
        assert data["content"] is not None
        assert "sections" in data["content"]
        assert data["confidence"] is not None
        assert "overall" in data["confidence"]
        assert data["redTeamReport"] is not None
        assert "entries" in data["redTeamReport"]

    async def test_get_document_not_found(self, client: AsyncClient):
        """Should return 404 for non-existent document."""
        response = await client.get("/api/documents/nonexistent-id")
        assert response.status_code == 404
        data = response.json()
        assert data["detail"]["code"] == "DOCUMENT_NOT_FOUND"

    async def test_get_document_with_metrics(
        self, client: AsyncClient, db_document: Document
    ):
        """Should include generation metrics."""
        response = await client.get(f"/api/documents/{db_document.id}")
        assert response.status_code == 200
        data = response.json()

        assert data["metrics"] is not None
        metrics = data["metrics"]
        assert "roundsCompleted" in metrics
        assert "totalCritiques" in metrics
        assert "timeElapsedMs" in metrics


class TestDeleteDocument:
    """Tests for DELETE /api/documents/{id}."""

    async def test_delete_document_success(
        self, client: AsyncClient, db_document: Document
    ):
        """Should delete a document."""
        response = await client.delete(f"/api/documents/{db_document.id}")
        assert response.status_code == 204

        # Verify deletion
        get_response = await client.get(f"/api/documents/{db_document.id}")
        assert get_response.status_code == 404

    async def test_delete_document_not_found(self, client: AsyncClient):
        """Should return 404 for non-existent document."""
        response = await client.delete("/api/documents/nonexistent-id")
        assert response.status_code == 404
        data = response.json()
        assert data["detail"]["code"] == "DOCUMENT_NOT_FOUND"


class TestDuplicateDocument:
    """Tests for POST /api/documents/{id}/duplicate."""

    async def test_duplicate_document_success(
        self, client: AsyncClient, db_document: Document
    ):
        """Should duplicate a document with default title."""
        response = await client.post(f"/api/documents/{db_document.id}/duplicate")
        assert response.status_code == 201
        data = response.json()

        assert data["id"] != db_document.id
        assert "(Copy)" in data["title"]
        assert data["status"] == "draft"  # Reset to draft
        assert data["type"] == db_document.type

    async def test_duplicate_document_custom_title(
        self, client: AsyncClient, db_document: Document
    ):
        """Should duplicate a document with custom title."""
        response = await client.post(
            f"/api/documents/{db_document.id}/duplicate",
            json={"newTitle": "My Custom Copy"},
        )
        assert response.status_code == 201
        data = response.json()

        assert data["title"] == "My Custom Copy"

    async def test_duplicate_document_not_found(self, client: AsyncClient):
        """Should return 404 for non-existent document."""
        response = await client.post("/api/documents/nonexistent-id/duplicate")
        assert response.status_code == 404


class TestApproveDocument:
    """Tests for POST /api/documents/{id}/approve."""

    async def test_approve_document_success(
        self, client: AsyncClient, db_document: Document
    ):
        """Should approve a document."""
        response = await client.post(f"/api/documents/{db_document.id}/approve")
        assert response.status_code == 200
        data = response.json()

        assert data["status"] == "approved"

    async def test_approve_document_with_notes(
        self, client: AsyncClient, db_document: Document
    ):
        """Should approve a document with review notes."""
        response = await client.post(
            f"/api/documents/{db_document.id}/approve",
            json={"reviewNotes": "Looks good after review"},
        )
        assert response.status_code == 200
        data = response.json()

        assert data["status"] == "approved"

    async def test_approve_document_not_found(self, client: AsyncClient):
        """Should return 404 for non-existent document."""
        response = await client.post("/api/documents/nonexistent-id/approve")
        assert response.status_code == 404


class TestRejectDocument:
    """Tests for POST /api/documents/{id}/reject."""

    async def test_reject_document_success(
        self, client: AsyncClient, db_document: Document
    ):
        """Should reject a document."""
        response = await client.post(f"/api/documents/{db_document.id}/reject")
        assert response.status_code == 200
        data = response.json()

        assert data["status"] == "rejected"

    async def test_reject_document_with_notes(
        self, client: AsyncClient, db_document: Document
    ):
        """Should reject a document with review notes."""
        response = await client.post(
            f"/api/documents/{db_document.id}/reject",
            json={"reviewNotes": "Needs more work on compliance section"},
        )
        assert response.status_code == 200
        data = response.json()

        assert data["status"] == "rejected"

    async def test_reject_document_not_found(self, client: AsyncClient):
        """Should return 404 for non-existent document."""
        response = await client.post("/api/documents/nonexistent-id/reject")
        assert response.status_code == 404


class TestExportDocument:
    """Tests for GET /api/documents/{id}/export."""

    async def test_export_document_pdf(
        self, client: AsyncClient, db_document: Document
    ):
        """Should export document as PDF."""
        response = await client.get(
            f"/api/documents/{db_document.id}/export?format=pdf"
        )
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/pdf"
        assert "attachment" in response.headers["content-disposition"]

    async def test_export_document_word(
        self, client: AsyncClient, db_document: Document
    ):
        """Should export document as Word."""
        response = await client.get(
            f"/api/documents/{db_document.id}/export?format=word"
        )
        assert response.status_code == 200
        assert "application/vnd.openxmlformats" in response.headers["content-type"]

    async def test_export_document_markdown(
        self, client: AsyncClient, db_document: Document
    ):
        """Should export document as Markdown."""
        response = await client.get(
            f"/api/documents/{db_document.id}/export?format=markdown"
        )
        assert response.status_code == 200
        assert response.headers["content-type"] == "text/markdown; charset=utf-8"

    async def test_export_document_default_format(
        self, client: AsyncClient, db_document: Document
    ):
        """Should default to PDF format."""
        response = await client.get(f"/api/documents/{db_document.id}/export")
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/pdf"

    async def test_export_document_not_found(self, client: AsyncClient):
        """Should return 404 for non-existent document."""
        response = await client.get("/api/documents/nonexistent-id/export")
        assert response.status_code == 404


class TestShareLinks:
    """Tests for share link endpoints."""

    async def test_create_share_link(
        self, client: AsyncClient, db_document: Document
    ):
        """Should create a share link."""
        response = await client.post(f"/api/documents/{db_document.id}/share")
        assert response.status_code == 201
        data = response.json()

        assert "id" in data
        assert "token" in data
        assert "url" in data
        assert data["documentId"] == db_document.id
        assert data["hasPassword"] is False
        assert data["expiresAt"] is None

    async def test_create_share_link_with_password(
        self, client: AsyncClient, db_document: Document
    ):
        """Should create a password-protected share link."""
        response = await client.post(
            f"/api/documents/{db_document.id}/share",
            json={"password": "secret123"},
        )
        assert response.status_code == 201
        data = response.json()

        assert data["hasPassword"] is True

    async def test_create_share_link_with_expiry(
        self, client: AsyncClient, db_document: Document
    ):
        """Should create an expiring share link."""
        response = await client.post(
            f"/api/documents/{db_document.id}/share",
            json={"expiresInDays": 7},
        )
        assert response.status_code == 201
        data = response.json()

        assert data["expiresAt"] is not None

    async def test_list_share_links(
        self, client: AsyncClient, db_document: Document
    ):
        """Should list share links for a document."""
        # Create some share links
        await client.post(f"/api/documents/{db_document.id}/share")
        await client.post(f"/api/documents/{db_document.id}/share")

        response = await client.get(f"/api/documents/{db_document.id}/share")
        assert response.status_code == 200
        data = response.json()

        assert len(data["shareLinks"]) == 2
        assert data["total"] == 2

    async def test_delete_share_link(
        self, client: AsyncClient, db_document: Document
    ):
        """Should delete a share link."""
        # Create a share link
        create_response = await client.post(f"/api/documents/{db_document.id}/share")
        share_link_id = create_response.json()["id"]

        # Delete it
        response = await client.delete(
            f"/api/documents/{db_document.id}/share/{share_link_id}"
        )
        assert response.status_code == 204

        # Verify deletion
        list_response = await client.get(f"/api/documents/{db_document.id}/share")
        assert list_response.json()["total"] == 0

    async def test_access_shared_document(
        self, client: AsyncClient, db_document: Document
    ):
        """Should access document via share link."""
        # Create a share link
        create_response = await client.post(f"/api/documents/{db_document.id}/share")
        token = create_response.json()["token"]

        # Access via token
        response = await client.get(f"/api/documents/shared/{token}")
        assert response.status_code == 200
        data = response.json()

        assert data["documentId"] == db_document.id

    async def test_access_shared_document_with_password(
        self, client: AsyncClient, db_document: Document
    ):
        """Should access password-protected document."""
        # Create password-protected share link
        create_response = await client.post(
            f"/api/documents/{db_document.id}/share",
            json={"password": "secret123"},
        )
        token = create_response.json()["token"]

        # Access without password should fail
        response = await client.get(f"/api/documents/shared/{token}")
        assert response.status_code == 401
        assert response.json()["detail"]["code"] == "PASSWORD_REQUIRED"

        # Access with correct password
        response = await client.get(f"/api/documents/shared/{token}?password=secret123")
        assert response.status_code == 200

        # Access with wrong password
        response = await client.get(f"/api/documents/shared/{token}?password=wrong")
        assert response.status_code == 401
        assert response.json()["detail"]["code"] == "INVALID_PASSWORD"

    async def test_access_invalid_share_link(self, client: AsyncClient):
        """Should return 404 for invalid share link token."""
        response = await client.get("/api/documents/shared/invalid-token")
        assert response.status_code == 404
        assert response.json()["detail"]["code"] == "SHARE_LINK_NOT_FOUND"


class TestHealthAndRoot:
    """Tests for health check and root endpoints."""

    async def test_health_check(self, client: AsyncClient):
        """Should return healthy status."""
        response = await client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data
        assert "version" in data

    async def test_root_endpoint(self, client: AsyncClient):
        """Should return API information."""
        response = await client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "name" in data
        assert "version" in data
        assert "docs" in data
