import { useState, useCallback } from 'react';
import type { CompanyProfile } from '../../types';
import { Modal, Button, ModalFooter } from '../ui';
import { ProfileForm, type ProfileFormData } from './ProfileForm';

interface ProfileModalProps {
  isOpen: boolean;
  onClose: () => void;
  profile?: CompanyProfile;
  onSubmit: (data: ProfileFormData) => void;
  isSubmitting?: boolean;
}

export function ProfileModal({
  isOpen,
  onClose,
  profile,
  onSubmit,
  isSubmitting = false,
}: ProfileModalProps) {
  const [showConfirmClose, setShowConfirmClose] = useState(false);

  const title = profile ? 'Edit Company Profile' : 'Create Company Profile';

  const handleClose = useCallback(() => {
    setShowConfirmClose(true);
  }, []);

  const handleConfirmClose = useCallback(() => {
    setShowConfirmClose(false);
    onClose();
  }, [onClose]);

  const handleCancelClose = useCallback(() => {
    setShowConfirmClose(false);
  }, []);

  return (
    <>
      <Modal isOpen={isOpen} onClose={handleClose} title={title} size="lg">
        <ProfileForm
          initialData={profile}
          onSubmit={onSubmit}
          onCancel={handleClose}
          isSubmitting={isSubmitting}
        />
      </Modal>

      {/* Confirmation dialog */}
      <Modal
        isOpen={showConfirmClose}
        onClose={handleCancelClose}
        title="Close Profile?"
        size="sm"
      >
        <p style={{ margin: '0 0 16px', color: 'var(--color-text-secondary)' }}>
          Are you sure you want to close? Any unsaved changes will be lost.
        </p>
        <ModalFooter>
          <Button variant="secondary" onClick={handleCancelClose}>
            Keep Editing
          </Button>
          <Button variant="danger" onClick={handleConfirmClose}>
            Close
          </Button>
        </ModalFooter>
      </Modal>
    </>
  );
}
