import { useParams, useNavigate } from 'react-router-dom';
import { useState, useEffect, useCallback, useMemo } from 'react';
import { MainWorkspace } from '../components/layout';
import { FinalOutputView } from '../components/final-output/FinalOutputView';
import { documentsApi } from '../api/documents';
import type { FinalOutput, DocumentType, Critique, Response } from '../types';
import './DocumentView.css';

export function DocumentViewPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [docData, setDocData] = useState<FinalOutput | null>(null);
  const [documentMeta, setDocumentMeta] = useState<{
    type: DocumentType;
    title: string;
  } | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function fetchDocument() {
      if (!id) {
        setError('No document ID provided');
        setLoading(false);
        return;
      }

      try {
        setLoading(true);
        setError(null);

        // Fetch the full document
        const doc = await documentsApi.get(id);
        if (!doc) {
          setError('Document not found');
          setLoading(false);
          return;
        }

        setDocData(doc);

        // Fetch document metadata from the list to get type and title
        const listResponse = await documentsApi.list({ limit: 100 });
        const meta = listResponse.documents.find((d) => d.id === id);
        if (meta) {
          setDocumentMeta({
            type: meta.type,
            title: meta.title,
          });
        } else {
          // Fallback if not found in list
          setDocumentMeta({
            type: 'capability-statement',
            title: `Document ${id}`,
          });
        }
      } catch (err) {
        console.error('Failed to fetch document:', err);
        setError(err instanceof Error ? err.message : 'Failed to load document');
      } finally {
        setLoading(false);
      }
    }

    fetchDocument();
  }, [id]);

  const handleExport = useCallback(
    async (format: 'word' | 'pdf' | 'markdown' | 'share') => {
      if (!id) return;

      try {
        const result = await documentsApi.export(id, format);

        if (format === 'share' && result.url) {
          await navigator.clipboard.writeText(result.url);
          alert('Share link copied to clipboard!');
        } else if (result.blob) {
          // Trigger download
          const url = URL.createObjectURL(result.blob);
          const a = document.createElement('a');
          a.href = url;
          a.download = `${documentMeta?.title || 'document'}.${format === 'word' ? 'docx' : format}`;
          document.body.appendChild(a);
          a.click();
          document.body.removeChild(a);
          URL.revokeObjectURL(url);
        }
      } catch (err) {
        console.error('Export failed:', err);
        alert('Export failed. Please try again.');
      }
    },
    [id, documentMeta]
  );

  const handleBack = useCallback(() => {
    navigate('/history');
  }, [navigate]);

  // Extract critiques and responses from red team report entries
  // This must be called before any early returns to satisfy React's Rules of Hooks
  const { critiques, responses } = useMemo(() => {
    const extractedCritiques: Critique[] = [];
    const extractedResponses: Response[] = [];

    if (docData?.redTeamReport?.entries) {
      docData.redTeamReport.entries.forEach((entry) => {
        if (entry.type === 'critique') {
          extractedCritiques.push({
            id: entry.id,
            agentId: entry.agentId,
            target: '',  // Not stored in entries
            severity: entry.severity || 'minor',
            content: entry.content,
            timestamp: entry.timestamp,
            round: entry.round,
            phase: entry.phase,
            status: entry.status || 'pending',
          });
        } else if (entry.type === 'response') {
          extractedResponses.push({
            id: entry.id,
            agentId: entry.agentId,
            critiqueId: '',  // Not directly linked in entries
            content: entry.content,
            accepted: true,
            timestamp: entry.timestamp,
            round: entry.round,
            phase: entry.phase,
          });
        }
      });
    }

    return { critiques: extractedCritiques, responses: extractedResponses };
  }, [docData]);

  if (loading) {
    return (
      <MainWorkspace title="Loading...">
        <div className="document-view-page__loading">
          <div className="document-view-page__spinner" />
          <p>Loading document...</p>
        </div>
      </MainWorkspace>
    );
  }

  if (error || !docData || !documentMeta) {
    return (
      <MainWorkspace title="Error">
        <div className="document-view-page__error">
          <h2>Unable to load document</h2>
          <p>{error || 'Document not found or has no content'}</p>
          <button onClick={handleBack} className="document-view-page__back-btn">
            Back to History
          </button>
        </div>
      </MainWorkspace>
    );
  }

  // Check if document has content
  const hasContent = docData.content?.sections && docData.content.sections.length > 0;

  if (!hasContent) {
    return (
      <MainWorkspace title={documentMeta.title}>
        <div className="document-view-page__empty">
          <h2>Document Not Yet Generated</h2>
          <p>
            This document exists but has not been generated yet, or the generation
            did not produce any content.
          </p>
          <button onClick={handleBack} className="document-view-page__back-btn">
            Back to History
          </button>
        </div>
      </MainWorkspace>
    );
  }

  return (
    <MainWorkspace title={documentMeta.title}>
      <div className="document-view-page">
        <div className="document-view-page__header">
          <button onClick={handleBack} className="document-view-page__back-btn">
            &larr; Back to History
          </button>
        </div>
        <FinalOutputView
          result={docData}
          documentType={documentMeta.type}
          title={documentMeta.title}
          critiques={critiques}
          responses={responses}
          agents={{}}
          onExport={handleExport}
          initialTab="document"
          className="document-view-page__content"
          hideInsights
        />
      </div>
    </MainWorkspace>
  );
}
