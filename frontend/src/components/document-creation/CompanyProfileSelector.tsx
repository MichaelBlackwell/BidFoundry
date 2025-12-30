import { useState } from 'react';
import type { CompanyProfile } from '../../types';
import { useProfiles, useCreateProfile } from '../../hooks/useProfiles';
import { naicsCodesToStrings } from '../../api/profiles';
import { ProfileModal, type ProfileFormData } from '../profiles';
import { Button } from '../ui';
import './CompanyProfileSelector.css';

interface CompanyProfileSelectorProps {
  value: string | null;
  onChange: (profileId: string | null) => void;
}

export function CompanyProfileSelector({ value, onChange }: CompanyProfileSelectorProps) {
  const { data: profiles = [], isLoading } = useProfiles();
  const createProfile = useCreateProfile();
  const [showCreateModal, setShowCreateModal] = useState(false);

  const selectedProfile = profiles.find((p: CompanyProfile) => p.id === value);

  const handleCreateProfile = async (data: ProfileFormData) => {
    try {
      const newProfile = await createProfile.mutateAsync(data);
      setShowCreateModal(false);
      onChange(newProfile.id);
    } catch (error) {
      console.error('Failed to create profile:', error);
    }
  };

  return (
    <div className="profile-selector">
      <h3 className="profile-selector__label">Company Profile</h3>
      <div className="profile-selector__controls">
        <select
          className="profile-selector__select"
          value={value || ''}
          onChange={(e) => onChange(e.target.value || null)}
          disabled={isLoading}
        >
          <option value="">Select a profile...</option>
          {profiles.map((profile: CompanyProfile) => (
            <option key={profile.id} value={profile.id}>
              {profile.name}
            </option>
          ))}
        </select>
        <span className="profile-selector__separator">or</span>
        <Button
          variant="secondary"
          size="sm"
          onClick={() => setShowCreateModal(true)}
        >
          + Create new
        </Button>
      </div>
      {selectedProfile && (
        <div className="profile-selector__preview">
          <div className="profile-selector__preview-name">{selectedProfile.name}</div>
          {selectedProfile.description && (
            <div className="profile-selector__preview-desc">{selectedProfile.description}</div>
          )}
          {selectedProfile.naicsCodes && selectedProfile.naicsCodes.length > 0 && (
            <div className="profile-selector__preview-codes">
              NAICS: {naicsCodesToStrings(selectedProfile.naicsCodes).join(', ')}
            </div>
          )}
        </div>
      )}
      <ProfileModal
        isOpen={showCreateModal}
        onClose={() => setShowCreateModal(false)}
        onSubmit={handleCreateProfile}
        isSubmitting={createProfile.isPending}
      />
    </div>
  );
}
