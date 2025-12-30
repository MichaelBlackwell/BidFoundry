/**
 * DocumentCard Component
 *
 * Displays a single document in the history list.
 * Shows document type, title, status, confidence, and provides action buttons.
 */

import { useNavigate } from 'react-router-dom';
import type { GeneratedDocument, DocumentType } from '../../types';
import { DOCUMENT_TYPE_LABELS } from '../../types';
import { Button } from '../ui';
import './DocumentCard.css';

interface DocumentCardProps {
  document: GeneratedDocument;
  onDelete: (document: GeneratedDocument) => void;
  onDuplicate: (document: GeneratedDocument) => void;
  onExport: (document: GeneratedDocument) => void;
  onPrefetch?: (documentId: string) => void;
}

const STATUS_CONFIG: Record<
  GeneratedDocument['status'],
  { label: string; className: string }
> = {
  draft: { label: 'Draft', className: 'status--draft' },
  approved: { label: 'Approved', className: 'status--approved' },
  rejected: { label: 'Rejected', className: 'status--rejected' },
};

const DOCUMENT_TYPE_ICONS: Record<DocumentType, string> = {
  'capability-statement': '📋',
  'swot-analysis': '🎯',
  'competitive-analysis': '🔍',
  'bd-pipeline-plan': '📊',
  'proposal-strategy': '📝',
  'go-to-market-strategy': '🚀',
  'teaming-strategy': '🤝',
};

export function DocumentCard({
  document,
  onDelete,
  onDuplicate,
  onExport,
  onPrefetch,
}: DocumentCardProps) {
  const navigate = useNavigate();
  const statusConfig = STATUS_CONFIG[document.status];

  const formatDate = (date: Date) => {
    return new Intl.DateTimeFormat('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
      hour: 'numeric',
      minute: '2-digit',
    }).format(new Date(date));
  };

  const formatRelativeDate = (date: Date) => {
    const now = new Date();
    const diff = now.getTime() - new Date(date).getTime();
    const minutes = Math.floor(diff / 60000);
    const hours = Math.floor(diff / 3600000);
    const days = Math.floor(diff / 86400000);

    if (minutes < 1) return 'Just now';
    if (minutes < 60) return `${minutes}m ago`;
    if (hours < 24) return `${hours}h ago`;
    if (days < 7) return `${days}d ago`;
    return formatDate(date);
  };

  const getConfidenceColor = (confidence: number): string => {
    if (confidence >= 80) return 'confidence--high';
    if (confidence >= 60) return 'confidence--medium';
    return 'confidence--low';
  };

  const handleCardClick = () => {
    navigate(`/documents/${document.id}`);
  };

  const handleMouseEnter = () => {
    onPrefetch?.(document.id);
  };

  const handleActionClick = (
    e: React.MouseEvent,
    action: (doc: GeneratedDocument) => void
  ) => {
    e.stopPropagation();
    action(document);
  };

  return (
    <article
      className="document-card"
      onClick={handleCardClick}
      onMouseEnter={handleMouseEnter}
      tabIndex={0}
      onKeyDown={(e) => e.key === 'Enter' && handleCardClick()}
      role="button"
      aria-label={`View ${document.title}`}
    >
      <div className="document-card__header">
        <div className="document-card__type">
          <span className="document-card__icon">
            {DOCUMENT_TYPE_ICONS[document.type]}
          </span>
          <span className="document-card__type-label">
            {DOCUMENT_TYPE_LABELS[document.type]}
          </span>
        </div>
        <span className={`document-card__status ${statusConfig.className}`}>
          {statusConfig.label}
        </span>
      </div>

      <h3 className="document-card__title">{document.title}</h3>

      <div className="document-card__meta">
        <div className="document-card__confidence">
          <span className="document-card__confidence-label">Confidence</span>
          <div className="document-card__confidence-bar">
            <div
              className={`document-card__confidence-fill ${getConfidenceColor(document.confidence)}`}
              style={{ width: `${document.confidence}%` }}
            />
          </div>
          <span
            className={`document-card__confidence-value ${getConfidenceColor(document.confidence)}`}
          >
            {document.confidence}%
          </span>
        </div>

        <div className="document-card__dates">
          <span
            className="document-card__date"
            title={`Created: ${formatDate(document.createdAt)}`}
          >
            Updated {formatRelativeDate(document.updatedAt)}
          </span>
        </div>
      </div>

      <div className="document-card__actions">
        <Button
          variant="ghost"
          size="sm"
          onClick={(e) => handleActionClick(e, () => navigate(`/documents/${document.id}`))}
          aria-label="View document"
        >
          View
        </Button>
        <Button
          variant="ghost"
          size="sm"
          onClick={(e) => handleActionClick(e, onDuplicate)}
          aria-label="Duplicate document"
        >
          Duplicate
        </Button>
        <Button
          variant="ghost"
          size="sm"
          onClick={(e) => handleActionClick(e, onExport)}
          aria-label="Export document"
        >
          Export
        </Button>
        <Button
          variant="ghost"
          size="sm"
          onClick={(e) => handleActionClick(e, onDelete)}
          aria-label="Delete document"
        >
          Delete
        </Button>
      </div>
    </article>
  );
}
