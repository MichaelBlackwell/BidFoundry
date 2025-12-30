import { useState, useCallback } from 'react';
import { MainWorkspace } from '../components/layout';
import { Button } from '../components/ui';
import {
  ProfileCard,
  ProfileModal,
  DeleteConfirmModal,
  type ProfileFormData,
} from '../components/profiles';
import {
  useProfiles,
  useCreateProfile,
  useUpdateProfile,
  useDeleteProfile,
} from '../hooks/useProfiles';
import type { CreateProfileInput, FullProfileData } from '../api/profiles';
import type { CompanyProfile } from '../types';
import './CompanyProfiles.css';

/**
 * Convert ProfileFormData to API input format.
 * Packages all extended fields into fullProfile for backend storage.
 */
function formDataToApiInput(data: ProfileFormData): Omit<CreateProfileInput, 'id'> {
  // Build the fullProfile object with all extended fields
  const fullProfile: FullProfileData = {
    // Basic Information
    ueiNumber: data.ueiNumber || undefined,
    cageCode: data.cageCode || undefined,

    // Company Fundamentals
    formationDate: data.formationDate || undefined,
    businessStatus: data.businessStatus || undefined,
    fiscalYearEnd: data.fiscalYearEnd || undefined,

    // Size and Structure
    employeeCount: data.employeeCount ? parseInt(data.employeeCount, 10) : undefined,
    employeeHeadcount: data.employeeHeadcount ? parseInt(data.employeeHeadcount, 10) : undefined,
    annualRevenue: data.annualRevenue ? parseFloat(data.annualRevenue) : undefined,
    revenueIsYtd: data.revenueIsYtd || undefined,

    // Principal Address
    principalAddress: data.principalAddress || undefined,

    // Ownership & Control
    ownershipStructure: data.ownershipStructure?.length ? data.ownershipStructure : undefined,
    managementTeam: data.managementTeam?.length ? data.managementTeam : undefined,

    // Socioeconomic Status
    veteranOwned: data.veteranOwned || undefined,
    serviceDisabledVeteranOwned: data.serviceDisabledVeteranOwned || undefined,
    womanOwned: data.womanOwned || undefined,
    economicallyDisadvantagedWomanOwned: data.economicallyDisadvantagedWomanOwned || undefined,
    disadvantagedBusiness: data.disadvantagedBusiness || undefined,

    // Certification & Compliance
    samRegistrationStatus: data.samRegistrationStatus || undefined,
    samRegistrationDate: data.samRegistrationDate || undefined,
    samExpirationDate: data.samExpirationDate || undefined,

    // Federal Contracting History
    federalContractingHistory: data.federalContractingHistory || undefined,

    // HUBZone
    hubzoneInfo: data.hubzoneInfo || undefined,
  };

  return {
    name: data.name,
    description: data.description || undefined,
    naicsCodes: data.naicsCodes,
    certifications: data.certifications,
    pastPerformance: data.pastPerformance,
    fullProfile,
  };
}

export function CompanyProfilesPage() {
  const { data: profiles, isLoading, error } = useProfiles();
  const createProfile = useCreateProfile();
  const updateProfile = useUpdateProfile();
  const deleteProfile = useDeleteProfile();

  const [isModalOpen, setIsModalOpen] = useState(false);
  const [isDeleteModalOpen, setIsDeleteModalOpen] = useState(false);
  const [selectedProfile, setSelectedProfile] = useState<CompanyProfile | null>(null);

  const handleCreate = useCallback(() => {
    setSelectedProfile(null);
    setIsModalOpen(true);
  }, []);

  const handleEdit = useCallback((profile: CompanyProfile) => {
    setSelectedProfile(profile);
    setIsModalOpen(true);
  }, []);

  const handleDelete = useCallback((profile: CompanyProfile) => {
    setSelectedProfile(profile);
    setIsDeleteModalOpen(true);
  }, []);

  const handleCloseModal = useCallback(() => {
    setIsModalOpen(false);
    setSelectedProfile(null);
  }, []);

  const handleCloseDeleteModal = useCallback(() => {
    setIsDeleteModalOpen(false);
    setSelectedProfile(null);
  }, []);

  const handleSubmit = useCallback(
    async (data: ProfileFormData) => {
      const apiInput = formDataToApiInput(data);
      if (selectedProfile) {
        await updateProfile.mutateAsync({ id: selectedProfile.id, ...apiInput });
      } else {
        await createProfile.mutateAsync(apiInput);
      }
      handleCloseModal();
    },
    [selectedProfile, createProfile, updateProfile, handleCloseModal]
  );

  const handleConfirmDelete = useCallback(async () => {
    if (selectedProfile) {
      await deleteProfile.mutateAsync(selectedProfile.id);
      handleCloseDeleteModal();
    }
  }, [selectedProfile, deleteProfile, handleCloseDeleteModal]);

  if (error) {
    return (
      <MainWorkspace title="Company Profiles">
        <div className="profiles-error">
          <p>Failed to load profiles. Please try again.</p>
          <Button onClick={() => window.location.reload()}>Reload</Button>
        </div>
      </MainWorkspace>
    );
  }

  return (
    <MainWorkspace title="Company Profiles">
      <div className="profiles-page">
        <div className="profiles-page__header">
          <p className="profiles-page__description">
            Manage your company profiles. Each profile contains information used to generate
            tailored strategy documents.
          </p>
          <Button onClick={handleCreate}>+ New Profile</Button>
        </div>

        {isLoading ? (
          <div className="profiles-loading">
            <div className="profiles-loading__spinner" />
            <p>Loading profiles...</p>
          </div>
        ) : profiles && profiles.length > 0 ? (
          <div className="profiles-grid">
            {profiles.map((profile) => (
              <ProfileCard
                key={profile.id}
                profile={profile}
                onEdit={handleEdit}
                onDelete={handleDelete}
              />
            ))}
          </div>
        ) : (
          <div className="profiles-empty">
            <div className="profiles-empty__icon">+</div>
            <h3>No profiles yet</h3>
            <p>Create your first company profile to start generating strategy documents.</p>
            <Button onClick={handleCreate}>Create Profile</Button>
          </div>
        )}
      </div>

      <ProfileModal
        isOpen={isModalOpen}
        onClose={handleCloseModal}
        profile={selectedProfile ?? undefined}
        onSubmit={handleSubmit}
        isSubmitting={createProfile.isPending || updateProfile.isPending}
      />

      <DeleteConfirmModal
        isOpen={isDeleteModalOpen}
        onClose={handleCloseDeleteModal}
        profile={selectedProfile}
        onConfirm={handleConfirmDelete}
        isDeleting={deleteProfile.isPending}
      />
    </MainWorkspace>
  );
}
