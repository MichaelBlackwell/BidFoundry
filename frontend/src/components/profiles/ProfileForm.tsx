import { useState, useCallback } from 'react';
import type {
  CompanyProfile,
  BusinessStatus,
  Address,
  OwnershipStake,
  OwnershipType,
  ManagementMember,
  HUBZoneInfo,
  FederalContractingHistory,
} from '../../types';
import {
  naicsCodesToStrings,
  certificationsToStrings,
  pastPerformanceToStrings,
} from '../../api/profiles';
import { Input, Textarea, TagInput, Button, ModalFooter, Select, Checkbox } from '../ui';
import './ProfileForm.css';

// Extended form data with all expanded fields
export interface ProfileFormData {
  // Basic Information
  name: string;
  description: string;
  ueiNumber: string;
  cageCode: string;

  // Company Fundamentals
  formationDate: string;
  businessStatus: BusinessStatus;
  fiscalYearEnd: string;

  // Size and Structure
  employeeCount: string;
  employeeHeadcount: string;
  annualRevenue: string;
  revenueIsYtd: boolean;

  // Principal Address
  principalAddress: Address | null;

  // Ownership & Control
  ownershipStructure: OwnershipStake[];
  managementTeam: ManagementMember[];

  // Socioeconomic Status
  veteranOwned: boolean;
  serviceDisabledVeteranOwned: boolean;
  womanOwned: boolean;
  economicallyDisadvantagedWomanOwned: boolean;
  disadvantagedBusiness: boolean;

  // Certification & Compliance
  samRegistrationStatus: string;
  samRegistrationDate: string;
  samExpirationDate: string;

  // Federal Contracting History
  federalContractingHistory: FederalContractingHistory | null;

  // HUBZone
  hubzoneInfo: HUBZoneInfo | null;

  // GovCon Specific (existing)
  naicsCodes: string[];
  certifications: string[];
  pastPerformance: string[];
}

interface ProfileFormProps {
  initialData?: CompanyProfile;
  onSubmit: (data: ProfileFormData) => void;
  onCancel: () => void;
  isSubmitting?: boolean;
}

const BUSINESS_STATUS_OPTIONS = [
  { value: 'Active', label: 'Active' },
  { value: 'Startup', label: 'Startup' },
  { value: 'Pre-Revenue', label: 'Pre-Revenue' },
  { value: 'Dormant', label: 'Dormant' },
  { value: 'Dissolved', label: 'Dissolved' },
];

const SAM_STATUS_OPTIONS = [
  { value: '', label: 'Select status...' },
  { value: 'Active', label: 'Active' },
  { value: 'Inactive', label: 'Inactive' },
  { value: 'Pending', label: 'Pending' },
  { value: 'Not Registered', label: 'Not Registered' },
];

const OWNERSHIP_TYPE_OPTIONS = [
  { value: 'Member', label: 'Member (LLC)' },
  { value: 'Shareholder', label: 'Shareholder (Corp)' },
  { value: 'Partner', label: 'Partner' },
  { value: 'Sole Proprietor', label: 'Sole Proprietor' },
];

interface FormSectionProps {
  title: string;
  children: React.ReactNode;
  defaultExpanded?: boolean;
}

function FormSection({ title, children, defaultExpanded = false }: FormSectionProps) {
  const [isExpanded, setIsExpanded] = useState(defaultExpanded);

  return (
    <div className={`profile-form__section ${isExpanded ? 'profile-form__section--expanded' : ''}`}>
      <button
        type="button"
        className="profile-form__section-header"
        onClick={() => setIsExpanded(!isExpanded)}
        aria-expanded={isExpanded}
      >
        <span className="profile-form__section-title">{title}</span>
        <span className="profile-form__section-icon">{isExpanded ? '−' : '+'}</span>
      </button>
      {isExpanded && <div className="profile-form__section-content">{children}</div>}
    </div>
  );
}

export function ProfileForm({
  initialData,
  onSubmit,
  onCancel,
  isSubmitting = false,
}: ProfileFormProps) {
  const [formData, setFormData] = useState<ProfileFormData>({
    // Basic Information
    name: initialData?.name ?? '',
    description: initialData?.description ?? '',
    ueiNumber: initialData?.ueiNumber ?? '',
    cageCode: initialData?.cageCode ?? '',

    // Company Fundamentals
    formationDate: initialData?.formationDate ?? '',
    businessStatus: initialData?.businessStatus ?? 'Active',
    fiscalYearEnd: initialData?.fiscalYearEnd ?? '',

    // Size and Structure
    employeeCount: initialData?.employeeCount?.toString() ?? '',
    employeeHeadcount: initialData?.employeeHeadcount?.toString() ?? '',
    annualRevenue: initialData?.annualRevenue?.toString() ?? '',
    revenueIsYtd: initialData?.revenueIsYtd ?? false,

    // Principal Address
    principalAddress: initialData?.principalAddress ?? null,

    // Ownership & Control
    ownershipStructure: initialData?.ownershipStructure ?? [],
    managementTeam: initialData?.managementTeam ?? [],

    // Socioeconomic Status
    veteranOwned: initialData?.veteranOwned ?? false,
    serviceDisabledVeteranOwned: initialData?.serviceDisabledVeteranOwned ?? false,
    womanOwned: initialData?.womanOwned ?? false,
    economicallyDisadvantagedWomanOwned: initialData?.economicallyDisadvantagedWomanOwned ?? false,
    disadvantagedBusiness: initialData?.disadvantagedBusiness ?? false,

    // Certification & Compliance
    samRegistrationStatus: initialData?.samRegistrationStatus ?? '',
    samRegistrationDate: initialData?.samRegistrationDate ?? '',
    samExpirationDate: initialData?.samExpirationDate ?? '',

    // Federal Contracting History
    federalContractingHistory: initialData?.federalContractingHistory ?? null,

    // HUBZone
    hubzoneInfo: initialData?.hubzoneInfo ?? null,

    // GovCon Specific
    naicsCodes: naicsCodesToStrings(initialData?.naicsCodes),
    certifications: certificationsToStrings(initialData?.certifications),
    pastPerformance: pastPerformanceToStrings(initialData?.pastPerformance),
  });

  const [errors, setErrors] = useState<Partial<Record<keyof ProfileFormData, string>>>({});

  const validate = useCallback((): boolean => {
    const newErrors: Partial<Record<keyof ProfileFormData, string>> = {};

    if (!formData.name.trim()) {
      newErrors.name = 'Company name is required';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  }, [formData.name]);

  const handleSubmit = useCallback(() => {
    if (validate()) {
      onSubmit(formData);
    }
  }, [formData, onSubmit, validate]);

  const updateField = <K extends keyof ProfileFormData>(
    field: K,
    value: ProfileFormData[K]
  ) => {
    setFormData((prev) => ({ ...prev, [field]: value }));
    if (errors[field]) {
      setErrors((prev) => ({ ...prev, [field]: undefined }));
    }
  };

  const updateAddress = (field: keyof Address, value: string) => {
    setFormData((prev) => ({
      ...prev,
      principalAddress: {
        street1: prev.principalAddress?.street1 ?? '',
        city: prev.principalAddress?.city ?? '',
        state: prev.principalAddress?.state ?? '',
        zipCode: prev.principalAddress?.zipCode ?? '',
        ...prev.principalAddress,
        [field]: value,
      },
    }));
  };

  // Ownership management
  const addOwner = () => {
    const newOwner: OwnershipStake = {
      name: '',
      ownershipType: 'Member' as OwnershipType,
      percentage: 0,
    };
    updateField('ownershipStructure', [...formData.ownershipStructure, newOwner]);
  };

  const updateOwner = (index: number, field: keyof OwnershipStake, value: string | number | boolean) => {
    const updated = [...formData.ownershipStructure];
    updated[index] = { ...updated[index], [field]: value };
    updateField('ownershipStructure', updated);
  };

  const removeOwner = (index: number) => {
    updateField('ownershipStructure', formData.ownershipStructure.filter((_, i) => i !== index));
  };

  // Management team
  const addManager = () => {
    const newManager: ManagementMember = {
      name: '',
      title: '',
    };
    updateField('managementTeam', [...formData.managementTeam, newManager]);
  };

  const updateManager = (index: number, field: keyof ManagementMember, value: string) => {
    const updated = [...formData.managementTeam];
    updated[index] = { ...updated[index], [field]: value };
    updateField('managementTeam', updated);
  };

  const removeManager = (index: number) => {
    updateField('managementTeam', formData.managementTeam.filter((_, i) => i !== index));
  };

  return (
    <div className="profile-form">
      <div className="profile-form__fields">
        {/* Basic Information - Always Expanded */}
        <FormSection title="Basic Information" defaultExpanded>
          <Input
            label="Company Name"
            value={formData.name}
            onChange={(e) => updateField('name', e.target.value)}
            placeholder="Enter company name"
            error={errors.name}
            required
            disabled={isSubmitting}
          />

          <Textarea
            label="Description"
            value={formData.description}
            onChange={(e) => updateField('description', e.target.value)}
            placeholder="Brief description of the company..."
            hint="Optional company overview for context in generated documents"
            disabled={isSubmitting}
          />

          <div className="profile-form__row">
            <Input
              label="UEI Number"
              value={formData.ueiNumber}
              onChange={(e) => updateField('ueiNumber', e.target.value)}
              placeholder="12-character UEI"
              hint="Unique Entity Identifier (SAM.gov)"
              disabled={isSubmitting}
            />
            <Input
              label="CAGE Code"
              value={formData.cageCode}
              onChange={(e) => updateField('cageCode', e.target.value)}
              placeholder="5-character code"
              hint="Commercial and Government Entity Code"
              disabled={isSubmitting}
            />
          </div>
        </FormSection>

        {/* Company Fundamentals */}
        <FormSection title="Company Fundamentals">
          <div className="profile-form__row">
            <Input
              label="Formation Date"
              type="date"
              value={formData.formationDate}
              onChange={(e) => updateField('formationDate', e.target.value)}
              hint="Legal incorporation/LLC formation date"
              disabled={isSubmitting}
            />
            <Select
              label="Business Status"
              value={formData.businessStatus}
              onChange={(e) => updateField('businessStatus', e.target.value as BusinessStatus)}
              options={BUSINESS_STATUS_OPTIONS}
              disabled={isSubmitting}
            />
          </div>

          <div className="profile-form__row">
            <Input
              label="Employee Count (FTE)"
              type="number"
              value={formData.employeeCount}
              onChange={(e) => updateField('employeeCount', e.target.value)}
              placeholder="Full-time equivalents"
              disabled={isSubmitting}
            />
            <Input
              label="Total Headcount"
              type="number"
              value={formData.employeeHeadcount}
              onChange={(e) => updateField('employeeHeadcount', e.target.value)}
              placeholder="Including contractors"
              disabled={isSubmitting}
            />
          </div>

          <div className="profile-form__row">
            <Input
              label="Annual Revenue ($)"
              type="number"
              value={formData.annualRevenue}
              onChange={(e) => updateField('annualRevenue', e.target.value)}
              placeholder="Last fiscal year"
              disabled={isSubmitting}
            />
            <div className="profile-form__checkbox-field">
              <Checkbox
                label="Revenue is YTD (pre-revenue company)"
                checked={formData.revenueIsYtd}
                onChange={(e) => updateField('revenueIsYtd', e.target.checked)}
                disabled={isSubmitting}
              />
            </div>
          </div>

          <Input
            label="Fiscal Year End"
            value={formData.fiscalYearEnd}
            onChange={(e) => updateField('fiscalYearEnd', e.target.value)}
            placeholder="e.g., December 31"
            disabled={isSubmitting}
          />
        </FormSection>

        {/* Principal Place of Business */}
        <FormSection title="Principal Place of Business">
          <Input
            label="Street Address"
            value={formData.principalAddress?.street1 ?? ''}
            onChange={(e) => updateAddress('street1', e.target.value)}
            placeholder="123 Main Street"
            disabled={isSubmitting}
          />
          <Input
            label="Street Address 2"
            value={formData.principalAddress?.street2 ?? ''}
            onChange={(e) => updateAddress('street2', e.target.value)}
            placeholder="Suite 100"
            disabled={isSubmitting}
          />
          <div className="profile-form__row profile-form__row--address">
            <Input
              label="City"
              value={formData.principalAddress?.city ?? ''}
              onChange={(e) => updateAddress('city', e.target.value)}
              placeholder="City"
              disabled={isSubmitting}
            />
            <Input
              label="State"
              value={formData.principalAddress?.state ?? ''}
              onChange={(e) => updateAddress('state', e.target.value)}
              placeholder="ST"
              disabled={isSubmitting}
            />
            <Input
              label="ZIP Code"
              value={formData.principalAddress?.zipCode ?? ''}
              onChange={(e) => updateAddress('zipCode', e.target.value)}
              placeholder="12345"
              disabled={isSubmitting}
            />
          </div>
        </FormSection>

        {/* Ownership & Control */}
        <FormSection title="Ownership & Control">
          <div className="profile-form__list-section">
            <div className="profile-form__list-header">
              <span className="profile-form__list-title">Ownership Structure</span>
              <Button
                type="button"
                variant="secondary"
                size="sm"
                onClick={addOwner}
                disabled={isSubmitting}
              >
                + Add Owner
              </Button>
            </div>

            {formData.ownershipStructure.map((owner, index) => (
              <div key={index} className="profile-form__list-item">
                <div className="profile-form__row">
                  <Input
                    label="Owner Name"
                    value={owner.name}
                    onChange={(e) => updateOwner(index, 'name', e.target.value)}
                    placeholder="Full name"
                    disabled={isSubmitting}
                  />
                  <Select
                    label="Type"
                    value={owner.ownershipType}
                    onChange={(e) => updateOwner(index, 'ownershipType', e.target.value)}
                    options={OWNERSHIP_TYPE_OPTIONS}
                    disabled={isSubmitting}
                  />
                  <Input
                    label="Percentage"
                    type="number"
                    value={owner.percentage.toString()}
                    onChange={(e) => updateOwner(index, 'percentage', parseFloat(e.target.value) || 0)}
                    placeholder="%"
                    disabled={isSubmitting}
                  />
                </div>
                <Input
                  label="Title"
                  value={owner.title ?? ''}
                  onChange={(e) => updateOwner(index, 'title', e.target.value)}
                  placeholder="e.g., Managing Member, CEO"
                  disabled={isSubmitting}
                />
                <div className="profile-form__owner-flags">
                  <Checkbox
                    label="Veteran"
                    checked={owner.isVeteran ?? false}
                    onChange={(e) => updateOwner(index, 'isVeteran', e.target.checked)}
                    disabled={isSubmitting}
                  />
                  <Checkbox
                    label="Service-Disabled Veteran"
                    checked={owner.isServiceDisabledVeteran ?? false}
                    onChange={(e) => updateOwner(index, 'isServiceDisabledVeteran', e.target.checked)}
                    disabled={isSubmitting}
                  />
                  <Checkbox
                    label="Woman"
                    checked={owner.isWoman ?? false}
                    onChange={(e) => updateOwner(index, 'isWoman', e.target.checked)}
                    disabled={isSubmitting}
                  />
                  <Checkbox
                    label="Disadvantaged (8(a))"
                    checked={owner.isDisadvantaged ?? false}
                    onChange={(e) => updateOwner(index, 'isDisadvantaged', e.target.checked)}
                    disabled={isSubmitting}
                  />
                </div>
                <Button
                  type="button"
                  variant="danger"
                  size="sm"
                  onClick={() => removeOwner(index)}
                  disabled={isSubmitting}
                >
                  Remove
                </Button>
              </div>
            ))}
            {formData.ownershipStructure.length === 0 && (
              <p className="profile-form__empty-message">No owners added yet.</p>
            )}
          </div>

          <div className="profile-form__divider" />

          <div className="profile-form__list-section">
            <div className="profile-form__list-header">
              <span className="profile-form__list-title">Management Team</span>
              <Button
                type="button"
                variant="secondary"
                size="sm"
                onClick={addManager}
                disabled={isSubmitting}
              >
                + Add Manager
              </Button>
            </div>

            {formData.managementTeam.map((manager, index) => (
              <div key={index} className="profile-form__list-item">
                <div className="profile-form__row">
                  <Input
                    label="Name"
                    value={manager.name}
                    onChange={(e) => updateManager(index, 'name', e.target.value)}
                    placeholder="Full name"
                    disabled={isSubmitting}
                  />
                  <Input
                    label="Title"
                    value={manager.title}
                    onChange={(e) => updateManager(index, 'title', e.target.value)}
                    placeholder="e.g., CEO, CFO"
                    disabled={isSubmitting}
                  />
                </div>
                <div className="profile-form__row">
                  <Input
                    label="Email"
                    type="email"
                    value={manager.email ?? ''}
                    onChange={(e) => updateManager(index, 'email', e.target.value)}
                    placeholder="email@company.com"
                    disabled={isSubmitting}
                  />
                  <Input
                    label="Phone"
                    type="tel"
                    value={manager.phone ?? ''}
                    onChange={(e) => updateManager(index, 'phone', e.target.value)}
                    placeholder="(555) 123-4567"
                    disabled={isSubmitting}
                  />
                </div>
                <Button
                  type="button"
                  variant="danger"
                  size="sm"
                  onClick={() => removeManager(index)}
                  disabled={isSubmitting}
                >
                  Remove
                </Button>
              </div>
            ))}
            {formData.managementTeam.length === 0 && (
              <p className="profile-form__empty-message">No managers added yet.</p>
            )}
          </div>

          <div className="profile-form__divider" />

          <div className="profile-form__socioeconomic">
            <span className="profile-form__label">Socioeconomic Status (for certification eligibility)</span>
            <div className="profile-form__checkbox-grid">
              <Checkbox
                label="Veteran-Owned (VOSB)"
                checked={formData.veteranOwned}
                onChange={(e) => updateField('veteranOwned', e.target.checked)}
                disabled={isSubmitting}
              />
              <Checkbox
                label="Service-Disabled Veteran-Owned (SDVOSB)"
                checked={formData.serviceDisabledVeteranOwned}
                onChange={(e) => updateField('serviceDisabledVeteranOwned', e.target.checked)}
                disabled={isSubmitting}
              />
              <Checkbox
                label="Woman-Owned (WOSB)"
                checked={formData.womanOwned}
                onChange={(e) => updateField('womanOwned', e.target.checked)}
                disabled={isSubmitting}
              />
              <Checkbox
                label="Economically Disadvantaged Woman-Owned (EDWOSB)"
                checked={formData.economicallyDisadvantagedWomanOwned}
                onChange={(e) => updateField('economicallyDisadvantagedWomanOwned', e.target.checked)}
                disabled={isSubmitting}
              />
              <Checkbox
                label="Disadvantaged Business (8(a))"
                checked={formData.disadvantagedBusiness}
                onChange={(e) => updateField('disadvantagedBusiness', e.target.checked)}
                disabled={isSubmitting}
              />
            </div>
          </div>
        </FormSection>

        {/* Certification & Compliance */}
        <FormSection title="Certification & Compliance">
          <div className="profile-form__row">
            <Select
              label="SAM.gov Registration Status"
              value={formData.samRegistrationStatus}
              onChange={(e) => updateField('samRegistrationStatus', e.target.value)}
              options={SAM_STATUS_OPTIONS}
              disabled={isSubmitting}
            />
          </div>
          <div className="profile-form__row">
            <Input
              label="SAM Registration Date"
              type="date"
              value={formData.samRegistrationDate}
              onChange={(e) => updateField('samRegistrationDate', e.target.value)}
              disabled={isSubmitting}
            />
            <Input
              label="SAM Expiration Date"
              type="date"
              value={formData.samExpirationDate}
              onChange={(e) => updateField('samExpirationDate', e.target.value)}
              disabled={isSubmitting}
            />
          </div>

          <div className="profile-form__divider" />

          <div className="profile-form__field">
            <label className="profile-form__label">Current SBA Certifications</label>
            <TagInput
              value={formData.certifications}
              onChange={(tags) => updateField('certifications', tags)}
              placeholder="e.g., 8(a), HUBZone, SDVOSB"
              disabled={isSubmitting}
            />
            <span className="profile-form__hint">
              Small business and other certifications with expiration dates
            </span>
          </div>
        </FormSection>

        {/* GovCon Specific */}
        <FormSection title="GovCon Specific">
          <div className="profile-form__field">
            <label className="profile-form__label">NAICS Codes</label>
            <TagInput
              value={formData.naicsCodes}
              onChange={(tags) => updateField('naicsCodes', tags)}
              placeholder="Add NAICS code and press Enter"
              disabled={isSubmitting}
            />
            <span className="profile-form__hint">
              Primary NAICS codes for government contracting
            </span>
          </div>

          <div className="profile-form__field">
            <label className="profile-form__label">Past Performance</label>
            <TagInput
              value={formData.pastPerformance}
              onChange={(tags) => updateField('pastPerformance', tags)}
              placeholder="Add contract name or description"
              disabled={isSubmitting}
            />
            <span className="profile-form__hint">
              Key past performance references
            </span>
          </div>
        </FormSection>

        {/* Geographic Information (HUBZone) */}
        <FormSection title="Geographic Information (HUBZone)">
          <Checkbox
            label="Principal office is located in a HUBZone"
            checked={formData.hubzoneInfo?.principalOfficeInHubzone ?? false}
            onChange={(e) => {
              const current = formData.hubzoneInfo ?? { principalOfficeInHubzone: false };
              updateField('hubzoneInfo', { ...current, principalOfficeInHubzone: e.target.checked });
            }}
            disabled={isSubmitting}
          />
          <Input
            label="HUBZone Designation"
            value={formData.hubzoneInfo?.hubzoneDesignation ?? ''}
            onChange={(e) => {
              const current = formData.hubzoneInfo ?? { principalOfficeInHubzone: false };
              updateField('hubzoneInfo', { ...current, hubzoneDesignation: e.target.value });
            }}
            placeholder="e.g., Qualified Census Tract, Redesignated Area"
            hint="Type of HUBZone designation if applicable"
            disabled={isSubmitting}
          />
          <p className="profile-form__hint profile-form__hint--block">
            Employee residence locations for HUBZone percentage calculations can be tracked
            via the detailed profile editor (coming soon).
          </p>
        </FormSection>
      </div>

      <ModalFooter>
        <Button type="button" variant="secondary" onClick={onCancel} disabled={isSubmitting}>
          Cancel
        </Button>
        <Button type="button" onClick={handleSubmit} loading={isSubmitting}>
          {initialData ? 'Update Profile' : 'Create Profile'}
        </Button>
      </ModalFooter>
    </div>
  );
}
