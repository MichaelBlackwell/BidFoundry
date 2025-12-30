/**
 * useDocuments Hook
 *
 * React Query hooks for document management.
 * Provides data fetching, caching, and mutations for document operations.
 */

import { useQuery, useMutation, useQueryClient, useInfiniteQuery } from '@tanstack/react-query';
import { documentsApi, type DocumentsListParams } from '../api/documents';
import type { ExportFormat } from '../types';

// Query keys for cache management
export const DOCUMENTS_KEY = ['documents'] as const;
export const DOCUMENT_KEY = (id: string) => ['document', id] as const;

// ============================================================================
// Query Hooks
// ============================================================================

/**
 * Fetch paginated list of documents with filtering
 */
export function useDocuments(params?: DocumentsListParams) {
  return useQuery({
    queryKey: [...DOCUMENTS_KEY, params],
    queryFn: () => documentsApi.list(params),
    staleTime: 30000, // Consider data fresh for 30 seconds
  });
}

/**
 * Fetch documents with infinite scroll pagination
 */
export function useInfiniteDocuments(params?: Omit<DocumentsListParams, 'offset'>) {
  const limit = params?.limit || 20;

  return useInfiniteQuery({
    queryKey: [...DOCUMENTS_KEY, 'infinite', params],
    queryFn: ({ pageParam = 0 }) =>
      documentsApi.list({ ...params, limit, offset: pageParam }),
    initialPageParam: 0,
    getNextPageParam: (lastPage, allPages) => {
      if (!lastPage.hasMore) return undefined;
      return allPages.length * limit;
    },
    staleTime: 30000,
  });
}

/**
 * Fetch a single document by ID
 */
export function useDocument(documentId: string | null) {
  return useQuery({
    queryKey: DOCUMENT_KEY(documentId || ''),
    queryFn: () => (documentId ? documentsApi.get(documentId) : null),
    enabled: !!documentId,
    staleTime: 60000, // Document details are fresh for 1 minute
  });
}

// ============================================================================
// Mutation Hooks
// ============================================================================

/**
 * Delete a document
 */
export function useDeleteDocument() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (documentId: string) => documentsApi.delete(documentId),
    onSuccess: (_, documentId) => {
      // Remove from cache
      queryClient.removeQueries({ queryKey: DOCUMENT_KEY(documentId) });
      // Invalidate list queries to refetch
      queryClient.invalidateQueries({ queryKey: DOCUMENTS_KEY });
    },
  });
}

/**
 * Duplicate a document
 */
export function useDuplicateDocument() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (documentId: string) => documentsApi.duplicate(documentId),
    onSuccess: () => {
      // Invalidate list queries to show the new document
      queryClient.invalidateQueries({ queryKey: DOCUMENTS_KEY });
    },
  });
}

/**
 * Update document status (approve/reject)
 */
export function useUpdateDocumentStatus() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      documentId,
      status,
      notes,
    }: {
      documentId: string;
      status: 'approved' | 'rejected';
      notes?: string;
    }) => documentsApi.updateStatus(documentId, status, notes),
    onSuccess: (updatedDoc) => {
      // Update the document in cache
      queryClient.setQueryData(DOCUMENT_KEY(updatedDoc.id), (old: unknown) => {
        if (!old) return old;
        return { ...old, status: updatedDoc.status };
      });
      // Invalidate list queries
      queryClient.invalidateQueries({ queryKey: DOCUMENTS_KEY });
    },
  });
}

/**
 * Export a document
 */
export function useExportDocument() {
  return useMutation({
    mutationFn: ({
      documentId,
      format,
    }: {
      documentId: string;
      format: ExportFormat;
    }) => documentsApi.export(documentId, format),
    onSuccess: (result, { format }) => {
      if (result.blob) {
        // Trigger download for blob results
        const url = URL.createObjectURL(result.blob);
        const link = document.createElement('a');
        link.href = url;
        link.download = `document.${format === 'word' ? 'docx' : format}`;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        URL.revokeObjectURL(url);
      } else if (result.url) {
        // Copy share URL to clipboard
        navigator.clipboard.writeText(result.url);
      }
    },
  });
}

// ============================================================================
// Utility Hooks
// ============================================================================

/**
 * Prefetch a document for faster navigation
 */
export function usePrefetchDocument() {
  const queryClient = useQueryClient();

  return (documentId: string) => {
    queryClient.prefetchQuery({
      queryKey: DOCUMENT_KEY(documentId),
      queryFn: () => documentsApi.get(documentId),
      staleTime: 60000,
    });
  };
}

/**
 * Invalidate all document caches (useful after generation completes)
 */
export function useInvalidateDocuments() {
  const queryClient = useQueryClient();

  return () => {
    queryClient.invalidateQueries({ queryKey: DOCUMENTS_KEY });
  };
}
