/**
 * History Page
 *
 * Document history list view with filtering, sorting, and document management.
 * Part of Chunk F11 - History and Document List.
 */

import { useState, useCallback, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import { MainWorkspace } from '../components/layout';
import {
  DocumentList,
  DocumentFilters,
  DEFAULT_FILTER_VALUES,
  type DocumentFilterValues,
} from '../components/document-history';
import { Button } from '../components/ui';
import {
  useDocuments,
  useDeleteDocument,
  useDuplicateDocument,
  useExportDocument,
  usePrefetchDocument,
} from '../hooks/useDocuments';
import type { DocumentType, ExportFormat } from '../types';
import './History.css';

export function HistoryPage() {
  const navigate = useNavigate();
  const [filters, setFilters] = useState<DocumentFilterValues>(DEFAULT_FILTER_VALUES);

  // Build query params from filters
  const queryParams = useMemo(() => {
    return {
      status: filters.status !== 'all' ? filters.status : undefined,
      type: filters.type !== 'all' ? (filters.type as DocumentType) : undefined,
      search: filters.search || undefined,
      sortBy: filters.sortBy,
      sortOrder: filters.sortOrder,
    };
  }, [filters]);

  // Fetch documents
  const { data, isLoading, error, refetch } = useDocuments(queryParams);

  // Mutations
  const deleteDocument = useDeleteDocument();
  const duplicateDocument = useDuplicateDocument();
  const exportDocument = useExportDocument();
  const prefetchDocument = usePrefetchDocument();

  // Get all documents for total count (unfiltered)
  const { data: allData } = useDocuments({});

  const handleDelete = useCallback(
    async (documentId: string) => {
      await deleteDocument.mutateAsync(documentId);
    },
    [deleteDocument]
  );

  const handleDuplicate = useCallback(
    async (documentId: string) => {
      const newDoc = await duplicateDocument.mutateAsync(documentId);
      // Optionally navigate to the new document
      navigate(`/documents/${newDoc.id}`);
    },
    [duplicateDocument, navigate]
  );

  const handleExport = useCallback(
    async (documentId: string, format: ExportFormat) => {
      await exportDocument.mutateAsync({ documentId, format });
    },
    [exportDocument]
  );

  const handleRetry = useCallback(() => {
    refetch();
  }, [refetch]);

  return (
    <MainWorkspace title="Document History">
      <div className="history-page">
        <div className="history-page__header">
          <div className="history-page__intro">
            <p className="history-page__description">
              View and manage all your generated strategy documents. Filter by status,
              type, or search by title.
            </p>
          </div>
          <div className="history-page__actions">
            <Button
              variant="primary"
              onClick={() => navigate('/new')}
            >
              + New Document
            </Button>
          </div>
        </div>

        <DocumentFilters
          values={filters}
          onChange={setFilters}
          totalCount={allData?.total}
          filteredCount={data?.total}
        />

        <DocumentList
          documents={data?.documents ?? []}
          isLoading={isLoading}
          error={error}
          onDelete={handleDelete}
          onDuplicate={handleDuplicate}
          onExport={handleExport}
          onPrefetch={prefetchDocument}
          onRetry={handleRetry}
        />

        {data?.hasMore && !isLoading && (
          <div className="history-page__load-more">
            <Button variant="secondary" onClick={() => {/* TODO: Load more */}}>
              Load More
            </Button>
          </div>
        )}
      </div>
    </MainWorkspace>
  );
}
