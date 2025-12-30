import type { CompanyProfile } from '../../types';
import { Modal, ModalFooter, Button } from '../ui';
import './DeleteConfirmModal.css';

interface DeleteConfirmModalProps {
  isOpen: boolean;
  onClose: () => void;
  profile: CompanyProfile | null;
  onConfirm: () => void;
  isDeleting?: boolean;
}

export function DeleteConfirmModal({
  isOpen,
  onClose,
  profile,
  onConfirm,
  isDeleting = false,
}: DeleteConfirmModalProps) {
  if (!profile) return null;

  return (
    <Modal isOpen={isOpen} onClose={onClose} title="Delete Profile" size="sm">
      <div className="delete-confirm">
        <p className="delete-confirm__message">
          Are you sure you want to delete <strong>{profile.name}</strong>? This action cannot be
          undone.
        </p>
        <p className="delete-confirm__warning">
          Any documents generated with this profile will still be accessible, but the profile
          will no longer be available for new documents.
        </p>
      </div>
      <ModalFooter>
        <Button variant="secondary" onClick={onClose} disabled={isDeleting}>
          Cancel
        </Button>
        <Button variant="danger" onClick={onConfirm} loading={isDeleting}>
          Delete Profile
        </Button>
      </ModalFooter>
    </Modal>
  );
}
