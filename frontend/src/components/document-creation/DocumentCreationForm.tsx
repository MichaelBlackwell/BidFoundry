import { useState, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import type { DocumentType, OpportunityContext, SwarmConfig, DocumentRequest } from '../../types';
import { useSwarmStore } from '../../stores/swarmStore';
import { useUIStore } from '../../stores/uiStore';
import { useWebSocket } from '../../providers/EnhancedWebSocketProvider';
import { generationApi } from '../../api/generation';
import { DocumentTypeSelector } from './DocumentTypeSelector';
import { CompanyProfileSelector } from './CompanyProfileSelector';
import { OpportunityContextForm } from './OpportunityContextForm';
import { SwarmConfigPanel } from './SwarmConfigPanel';
import { Button } from '../ui';
import './DocumentCreationForm.css';

const DOCUMENT_TYPE_LABELS: Record<DocumentType, string> = {
  'capability-statement': 'Capability Statement',
  'swot-analysis': 'SWOT Analysis',
  'bid-no-bid': 'Bid/No-Bid Analysis',
  'proposal-outline': 'Proposal Outline',
  'executive-summary': 'Executive Summary',
  'past-performance': 'Past Performance',
  'teaming-assessment': 'Teaming Assessment',
};

// Default swarm configuration
const DEFAULT_CONFIG: SwarmConfig = {
  intensity: 'medium',
  rounds: 3,
  consensus: 'supermajority',
  blueTeam: {
    'strategy-architect': true,
    'market-analyst': true,
    'compliance-navigator': true,
    'capture-strategist': true,
  },
  redTeam: {
    'devils-advocate': true,
    'competitor-simulator': true,
    'evaluator-simulator': true,
    'risk-assessor': true,
  },
  specialists: {
    'gsa-specialist': true,
    'past-performance-curator': true,
    'sbir-sttr-advisor': false,
    'pricing-strategist': false,
    'clearance-consultant': false,
  },
  riskTolerance: 'balanced',
  escalationThresholds: {
    confidenceMin: 70,
    criticalUnresolved: true,
    complianceUncertainty: true,
  },
};

export function DocumentCreationForm() {
  const navigate = useNavigate();
  const startGeneration = useSwarmStore((state) => state.startGeneration);
  const addDocumentTab = useUIStore((state) => state.addDocumentTab);
  const { connectionId, status: wsStatus } = useWebSocket();

  // Form state
  const [documentType, setDocumentType] = useState<DocumentType | null>(null);
  const [profileId, setProfileId] = useState<string | null>(null);
  const [opportunityContext, setOpportunityContext] = useState<OpportunityContext>({});
  const [config, setConfig] = useState<SwarmConfig>(DEFAULT_CONFIG);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState<string | null>(null);

  // Validation - also check WebSocket is connected
  const isValid = documentType !== null && profileId !== null;
  const canSubmit = isValid && wsStatus === 'connected' && connectionId !== null && !isSubmitting;

  const handleSubmit = useCallback(
    async (e: React.FormEvent) => {
      e.preventDefault();

      if (!isValid || !documentType || !profileId || !connectionId) return;

      const request: DocumentRequest = {
        documentType,
        companyProfileId: profileId,
        opportunityContext: Object.keys(opportunityContext).length > 0 ? opportunityContext : undefined,
        config,
      };

      setIsSubmitting(true);
      setSubmitError(null);

      try {
        // Call the REST API to start generation with the connectionId
        const response = await generationApi.startGeneration(request, connectionId);

        // Update local store state
        startGeneration(request);

        // Add a tab to the sidebar for this document generation
        const tabLabel = DOCUMENT_TYPE_LABELS[documentType] || 'Document';
        addDocumentTab({
          id: response.requestId,
          label: tabLabel,
          path: `/generate/${response.requestId}`,
        });

        // Navigate to the generation view with the request ID from the server
        navigate(`/generate/${response.requestId}`);
      } catch (error) {
        console.error('Failed to start generation:', error);
        setSubmitError(
          error instanceof Error
            ? error.message
            : 'Failed to start document generation. Please try again.'
        );
        setIsSubmitting(false);
      }
    },
    [documentType, profileId, opportunityContext, config, isValid, connectionId, startGeneration, addDocumentTab, navigate]
  );

  const handleCancel = useCallback(() => {
    navigate('/history');
  }, [navigate]);

  return (
    <form className="document-creation-form" onSubmit={handleSubmit}>
      <div className="document-creation-form__header">
        <h2>Create New Document</h2>
      </div>

      <div className="document-creation-form__body">
        <DocumentTypeSelector value={documentType} onChange={setDocumentType} />

        <CompanyProfileSelector value={profileId} onChange={setProfileId} />

        <OpportunityContextForm value={opportunityContext} onChange={setOpportunityContext} />

        <SwarmConfigPanel value={config} onChange={setConfig} documentType={documentType} />

        {submitError && (
          <div className="document-creation-form__error" role="alert">
            {submitError}
          </div>
        )}

        {wsStatus !== 'connected' && (
          <div className="document-creation-form__warning" role="status">
            Connecting to server...
          </div>
        )}
      </div>

      <div className="document-creation-form__footer">
        <Button type="button" variant="secondary" onClick={handleCancel} disabled={isSubmitting}>
          Cancel
        </Button>
        <Button type="submit" disabled={!canSubmit}>
          {isSubmitting ? 'Starting...' : 'Generate Document'}
        </Button>
      </div>
    </form>
  );
}
