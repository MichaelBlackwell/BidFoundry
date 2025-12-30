import { useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { MainWorkspace } from '../components/layout';
import { GenerationView } from '../components/generation-view';
import { useStatusAnnouncements } from '../hooks';

export function GenerationPage() {
  const { requestId } = useParams<{ requestId: string }>();
  const navigate = useNavigate();

  // Enable screen reader announcements for generation status
  useStatusAnnouncements({
    enabled: true,
    announceRounds: true,
    announcePhases: true,
    announceAgentActivity: true,
    announceConfidence: true,
  });

  // Handle generation completion - navigate to document view
  const handleComplete = useCallback(() => {
    // The GenerationView will trigger this when complete
    // We could navigate to the final output view or stay on this page
    console.log('Generation complete');
  }, []);

  // Handle cancellation - navigate back to new document
  const handleCancel = useCallback(() => {
    navigate('/new');
  }, [navigate]);

  // Handle section selection in preview
  const handleSectionSelect = useCallback((sectionId: string) => {
    // Could scroll to debate entry related to this section
    console.log('Section selected:', sectionId);
  }, []);

  return (
    <MainWorkspace title="Document Generation" fullWidth>
      <GenerationView
        requestId={requestId}
        onComplete={handleComplete}
        onCancel={handleCancel}
        onSectionSelect={handleSectionSelect}
      />
    </MainWorkspace>
  );
}
