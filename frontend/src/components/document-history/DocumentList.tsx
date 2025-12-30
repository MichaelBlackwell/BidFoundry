/**
 * DocumentList Component
 *
 * Displays a list of documents with loading, empty, and error states.
 * Handles document actions like delete, duplicate, and export.
 */

import { useState, useCallback } from 'react';
import type { GeneratedDocument, ExportFormat } from '../../types';
import { DocumentCard } from './DocumentCard';
import { Button } from '../ui';
import { Modal } from '../ui';
import './DocumentList.css';

interface DocumentListProps {
  documents: GeneratedDocument[];
  isLoading: boolean;
  error?: Error | null;
  onDelete: (documentId: string) => Promise<void>;
  onDuplicate: (documentId: string) => Promise<void>;
  onExport: (documentId: string, format: ExportFormat) => Promise<void>;
  onPrefetch?: (documentId: string) => void;
  onRetry?: () => void;
}

export function DocumentList({
  documents,
  isLoading,
  error,
  onDelete,
  onDuplicate,
  onExport,
  onPrefetch,
  onRetry,
}: DocumentListProps) {
  const [deleteTarget, setDeleteTarget] = useState<GeneratedDocument | null>(null);
  const [exportTarget, setExportTarget] = useState<GeneratedDocument | null>(null);
  const [actionLoading, setActionLoading] = useState<string | null>(null);

  const handleDeleteClick = useCallback((document: GeneratedDocument) => {
    setDeleteTarget(document);
  }, []);

  const handleDeleteConfirm = useCallback(async () => {
    if (!deleteTarget) return;
    setActionLoading('delete');
    try {
      await onDelete(deleteTarget.id);
    } finally {
      setActionLoading(null);
      setDeleteTarget(null);
    }
  }, [deleteTarget, onDelete]);

  const handleDuplicate = useCallback(
    async (document: GeneratedDocument) => {
      setActionLoading(`duplicate-${document.id}`);
      try {
        await onDuplicate(document.id);
      } finally {
        setActionLoading(null);
      }
    },
    [onDuplicate]
  );

  const handleExportClick = useCallback((document: GeneratedDocument) => {
    setExportTarget(document);
  }, []);

  const handleExportFormat = useCallback(
    async (format: ExportFormat) => {
      if (!exportTarget) return;
      setActionLoading(`export-${exportTarget.id}`);
      try {
        await onExport(exportTarget.id, format);
      } finally {
        setActionLoading(null);
        setExportTarget(null);
      }
    },
    [exportTarget, onExport]
  );

  // Loading state
  if (isLoading && documents.length === 0) {
    return (
      <div className="document-list document-list--loading">
        <div className="document-list__skeleton">
          {[1, 2, 3].map((i) => (
            <div key={i} className="document-list__skeleton-card">
              <div className="skeleton skeleton--header" />
              <div className="skeleton skeleton--title" />
              <div className="skeleton skeleton--meta" />
              <div className="skeleton skeleton--actions" />
            </div>
          ))}
        </div>
      </div>
    );
  }

  // Error state
  if (error) {
    return (
      <div className="document-list document-list--error">
        <div className="document-list__error-content">
          <span className="document-list__error-icon">!</span>
          <h3 className="document-list__error-title">Failed to load documents</h3>
          <p className="document-list__error-message">{error.message}</p>
          {onRetry && (
            <Button variant="primary" onClick={onRetry}>
              Try Again
            </Button>
          )}
        </div>
      </div>
    );
  }

  // Empty state
  if (documents.length === 0) {
    return (
      <div className="document-list document-list--empty">
        <div className="document-list__empty-content">
          <span className="document-list__empty-icon">📄</span>
          <h3 className="document-list__empty-title">No documents found</h3>
          <p className="document-list__empty-message">
            Documents you generate will appear here. Start by creating a new document.
          </p>
        </div>
      </div>
    );
  }

  return (
    <>
      <div className="document-list">
        <div className="document-list__grid">
          {documents.map((doc) => (
            <DocumentCard
              key={doc.id}
              document={doc}
              onDelete={handleDeleteClick}
              onDuplicate={handleDuplicate}
              onExport={handleExportClick}
              onPrefetch={onPrefetch}
            />
          ))}
        </div>

        {isLoading && (
          <div className="document-list__loading-more">
            <span className="document-list__spinner" />
            Loading more...
          </div>
        )}
      </div>

      {/* Delete Confirmation Modal */}
      <Modal
        isOpen={deleteTarget !== null}
        onClose={() => setDeleteTarget(null)}
        title="Delete Document"
      >
        <div className="document-list__modal-content">
          <p>
            Are you sure you want to delete <strong>{deleteTarget?.title}</strong>?
          </p>
          <p className="document-list__modal-warning">
            This action cannot be undone.
          </p>
          <div className="document-list__modal-actions">
            <Button
              variant="secondary"
              onClick={() => setDeleteTarget(null)}
              disabled={actionLoading === 'delete'}
            >
              Cancel
            </Button>
            <Button
              variant="danger"
              onClick={handleDeleteConfirm}
              loading={actionLoading === 'delete'}
            >
              Delete
            </Button>
          </div>
        </div>
      </Modal>

      {/* Export Format Modal */}
      <Modal
        isOpen={exportTarget !== null}
        onClose={() => setExportTarget(null)}
        title="Export Document"
      >
        <div className="document-list__modal-content">
          <p>Choose export format for <strong>{exportTarget?.title}</strong></p>
          <div className="document-list__export-options">
            <button
              type="button"
              className="document-list__export-option"
              onClick={() => handleExportFormat('word')}
              disabled={!!actionLoading}
            >
              <span className="document-list__export-icon">📄</span>
              <span className="document-list__export-label">Word (.docx)</span>
            </button>
            <button
              type="button"
              className="document-list__export-option"
              onClick={() => handleExportFormat('pdf')}
              disabled={!!actionLoading}
            >
              <span className="document-list__export-icon">📊</span>
              <span className="document-list__export-label">PDF</span>
            </button>
            <button
              type="button"
              className="document-list__export-option"
              onClick={() => handleExportFormat('markdown')}
              disabled={!!actionLoading}
            >
              <span className="document-list__export-icon">📋</span>
              <span className="document-list__export-label">Markdown</span>
            </button>
            <button
              type="button"
              className="document-list__export-option"
              onClick={() => handleExportFormat('share')}
              disabled={!!actionLoading}
            >
              <span className="document-list__export-icon">🔗</span>
              <span className="document-list__export-label">Share Link</span>
            </button>
          </div>
          {actionLoading?.startsWith('export-') && (
            <div className="document-list__export-loading">
              <span className="document-list__spinner" />
              Preparing export...
            </div>
          )}
        </div>
      </Modal>
    </>
  );
}
