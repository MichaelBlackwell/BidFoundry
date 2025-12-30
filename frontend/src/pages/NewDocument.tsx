import { MainWorkspace } from '../components/layout';
import { DocumentCreationForm } from '../components/document-creation';

export function NewDocumentPage() {
  return (
    <MainWorkspace title="Create New Document">
      <DocumentCreationForm />
    </MainWorkspace>
  );
}
