import type { CompanyProfile, NAICSCode, Certification, PastPerformance } from '../types';

// API base URL
const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000/api';

// Helper to convert simple string arrays to structured types
function stringsToNaicsCodes(codes: string[]): NAICSCode[] {
  return codes.map((code, index) => ({
    code,
    description: '',
    isPrimary: index === 0,
  }));
}

function stringsToCertifications(certs: string[]): Certification[] {
  return certs.map((cert) => ({
    certType: cert as Certification['certType'],
    issuingAuthority: '',
    issueDate: new Date().toISOString().split('T')[0],
  }));
}

function stringsToPastPerformance(items: string[]): PastPerformance[] {
  return items.map((item) => ({
    id: crypto.randomUUID(),
    contractNumber: '',
    contractName: item,
    agency: '',
    contractValue: 0,
    contractType: '',
    overallRating: 'Not Rated',
    naicsCodes: [],
    description: item,
    keyAccomplishments: [],
    relevanceKeywords: [],
  }));
}

// Helper to extract simple strings from structured types for display
export function naicsCodesToStrings(codes?: NAICSCode[]): string[] {
  return codes?.map((c) => c.code) ?? [];
}

export function certificationsToStrings(certs?: Certification[]): string[] {
  return certs?.map((c) => c.certType) ?? [];
}

export function pastPerformanceToStrings(items?: PastPerformance[]): string[] {
  return items?.map((pp) => pp.contractName || pp.description) ?? [];
}

// Full profile data for form submissions (all company fields)
export interface FullProfileData {
  // Basic Information
  ueiNumber?: string;
  cageCode?: string;

  // Company Fundamentals
  formationDate?: string;
  businessStatus?: string;
  fiscalYearEnd?: string;

  // Size and Structure
  employeeCount?: number;
  employeeHeadcount?: number;
  annualRevenue?: number;
  revenueIsYtd?: boolean;

  // Principal Address
  principalAddress?: {
    street1?: string;
    street2?: string;
    city?: string;
    state?: string;
    zipCode?: string;
    country?: string;
  } | null;

  // Ownership & Control
  ownershipStructure?: Array<{
    name: string;
    ownershipType: string;
    percentage: number;
    title?: string;
    isVeteran?: boolean;
    isServiceDisabledVeteran?: boolean;
    isWoman?: boolean;
    isDisadvantaged?: boolean;
  }>;
  managementTeam?: Array<{
    name: string;
    title: string;
    email?: string;
    phone?: string;
  }>;

  // Socioeconomic Status
  veteranOwned?: boolean;
  serviceDisabledVeteranOwned?: boolean;
  womanOwned?: boolean;
  economicallyDisadvantagedWomanOwned?: boolean;
  disadvantagedBusiness?: boolean;

  // Certification & Compliance
  samRegistrationStatus?: string;
  samRegistrationDate?: string;
  samExpirationDate?: string;

  // Federal Contracting History
  federalContractingHistory?: {
    hasFederalContracts?: boolean;
    totalContracts?: number;
    totalValue?: number;
    agencies?: string[];
  } | null;

  // HUBZone
  hubzoneInfo?: {
    principalOfficeInHubzone?: boolean;
    hubzoneDesignation?: string;
    employeeResidencePercentage?: number;
  } | null;
}

// Simple input format for form submissions
export interface CreateProfileInput {
  name: string;
  description?: string;
  naicsCodes?: string[];
  certifications?: string[];
  pastPerformance?: string[];
  fullProfile?: FullProfileData;
}

export interface UpdateProfileInput extends Partial<CreateProfileInput> {
  id: string;
}

// API response types (matching backend schemas)
interface ProfileApiResponse {
  id: string;
  name: string;
  description?: string;
  naicsCodes: string[];
  certifications: string[];
  pastPerformance: string[];
  fullProfile?: Record<string, unknown>;
  createdAt: string;
  updatedAt: string;
}

interface ProfileListApiResponse {
  profiles: ProfileApiResponse[];
  total: number;
}

// Transform API response to frontend CompanyProfile type
function transformApiProfile(apiProfile: ProfileApiResponse): CompanyProfile {
  const fullProfile = apiProfile.fullProfile || {};

  return {
    id: apiProfile.id,
    name: apiProfile.name,
    description: apiProfile.description,
    naicsCodes: stringsToNaicsCodes(apiProfile.naicsCodes || []),
    certifications: stringsToCertifications(apiProfile.certifications || []),
    pastPerformance: stringsToPastPerformance(apiProfile.pastPerformance || []),
    createdAt: new Date(apiProfile.createdAt),
    updatedAt: new Date(apiProfile.updatedAt),

    // Restore all fields from fullProfile
    ueiNumber: fullProfile.ueiNumber as string | undefined,
    cageCode: fullProfile.cageCode as string | undefined,
    formationDate: fullProfile.formationDate as string | undefined,
    businessStatus: fullProfile.businessStatus as CompanyProfile['businessStatus'],
    fiscalYearEnd: fullProfile.fiscalYearEnd as string | undefined,
    employeeCount: fullProfile.employeeCount as number | undefined,
    employeeHeadcount: fullProfile.employeeHeadcount as number | undefined,
    annualRevenue: fullProfile.annualRevenue as number | undefined,
    revenueIsYtd: fullProfile.revenueIsYtd as boolean | undefined,
    principalAddress: fullProfile.principalAddress as CompanyProfile['principalAddress'],
    ownershipStructure: fullProfile.ownershipStructure as CompanyProfile['ownershipStructure'],
    managementTeam: fullProfile.managementTeam as CompanyProfile['managementTeam'],
    veteranOwned: fullProfile.veteranOwned as boolean | undefined,
    serviceDisabledVeteranOwned: fullProfile.serviceDisabledVeteranOwned as boolean | undefined,
    womanOwned: fullProfile.womanOwned as boolean | undefined,
    economicallyDisadvantagedWomanOwned: fullProfile.economicallyDisadvantagedWomanOwned as boolean | undefined,
    disadvantagedBusiness: fullProfile.disadvantagedBusiness as boolean | undefined,
    samRegistrationStatus: fullProfile.samRegistrationStatus as string | undefined,
    samRegistrationDate: fullProfile.samRegistrationDate as string | undefined,
    samExpirationDate: fullProfile.samExpirationDate as string | undefined,
    federalContractingHistory: fullProfile.federalContractingHistory as CompanyProfile['federalContractingHistory'],
    hubzoneInfo: fullProfile.hubzoneInfo as CompanyProfile['hubzoneInfo'],
  };
}

async function handleResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    const message = errorData.detail?.message || errorData.detail || response.statusText;
    throw new Error(typeof message === 'string' ? message : JSON.stringify(message));
  }
  return response.json();
}

export const profilesApi = {
  async getAll(): Promise<CompanyProfile[]> {
    const response = await fetch(`${API_BASE}/profiles`, {
      method: 'GET',
      credentials: 'include',
    });
    const data = await handleResponse<ProfileListApiResponse>(response);
    return data.profiles.map(transformApiProfile);
  },

  async getById(id: string): Promise<CompanyProfile | null> {
    const response = await fetch(`${API_BASE}/profiles/${id}`, {
      method: 'GET',
      credentials: 'include',
    });
    if (response.status === 404) {
      return null;
    }
    const data = await handleResponse<ProfileApiResponse>(response);
    return transformApiProfile(data);
  },

  async create(input: CreateProfileInput): Promise<CompanyProfile> {
    const response = await fetch(`${API_BASE}/profiles`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      credentials: 'include',
      body: JSON.stringify({
        name: input.name,
        description: input.description,
        naicsCodes: input.naicsCodes || [],
        certifications: input.certifications || [],
        pastPerformance: input.pastPerformance || [],
        fullProfile: input.fullProfile || null,
      }),
    });
    const data = await handleResponse<ProfileApiResponse>(response);
    return transformApiProfile(data);
  },

  async update(input: UpdateProfileInput): Promise<CompanyProfile> {
    const response = await fetch(`${API_BASE}/profiles/${input.id}`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
      },
      credentials: 'include',
      body: JSON.stringify({
        name: input.name,
        description: input.description,
        naicsCodes: input.naicsCodes,
        certifications: input.certifications,
        pastPerformance: input.pastPerformance,
        fullProfile: input.fullProfile,
      }),
    });
    const data = await handleResponse<ProfileApiResponse>(response);
    return transformApiProfile(data);
  },

  async delete(id: string): Promise<void> {
    const response = await fetch(`${API_BASE}/profiles/${id}`, {
      method: 'DELETE',
      credentials: 'include',
    });
    if (!response.ok && response.status !== 204) {
      const errorData = await response.json().catch(() => ({}));
      const message = errorData.detail?.message || errorData.detail || response.statusText;
      throw new Error(typeof message === 'string' ? message : JSON.stringify(message));
    }
  },
};
