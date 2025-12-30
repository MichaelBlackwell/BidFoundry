/**
 * DocumentFilters Component
 *
 * Filter controls for the document history list.
 * Allows filtering by status, type, and search query.
 * Also provides sorting options.
 */

import { useState, useCallback, useEffect } from 'react';
import type { DocumentType, GeneratedDocument } from '../../types';
import { DOCUMENT_TYPE_LABELS } from '../../types';
import { Input } from '../ui';
import './DocumentFilters.css';

export interface DocumentFilterValues {
  search: string;
  status: GeneratedDocument['status'] | 'all';
  type: DocumentType | 'all';
  sortBy: 'updatedAt' | 'createdAt' | 'title' | 'confidence';
  sortOrder: 'asc' | 'desc';
}

interface DocumentFiltersProps {
  values: DocumentFilterValues;
  onChange: (values: DocumentFilterValues) => void;
  totalCount?: number;
  filteredCount?: number;
}

const STATUS_OPTIONS: Array<{ value: GeneratedDocument['status'] | 'all'; label: string }> = [
  { value: 'all', label: 'All Status' },
  { value: 'draft', label: 'Draft' },
  { value: 'approved', label: 'Approved' },
  { value: 'rejected', label: 'Rejected' },
];

const TYPE_OPTIONS: Array<{ value: DocumentType | 'all'; label: string }> = [
  { value: 'all', label: 'All Types' },
  ...Object.entries(DOCUMENT_TYPE_LABELS).map(([value, label]) => ({
    value: value as DocumentType,
    label,
  })),
];

const SORT_OPTIONS: Array<{ value: DocumentFilterValues['sortBy']; label: string }> = [
  { value: 'updatedAt', label: 'Last Updated' },
  { value: 'createdAt', label: 'Created' },
  { value: 'title', label: 'Title' },
  { value: 'confidence', label: 'Confidence' },
];

export function DocumentFilters({
  values,
  onChange,
  totalCount,
  filteredCount,
}: DocumentFiltersProps) {
  const [searchInput, setSearchInput] = useState(values.search);

  // Debounce search input
  useEffect(() => {
    const timer = setTimeout(() => {
      if (searchInput !== values.search) {
        onChange({ ...values, search: searchInput });
      }
    }, 300);
    return () => clearTimeout(timer);
  }, [searchInput, values, onChange]);

  const handleStatusChange = useCallback(
    (e: React.ChangeEvent<HTMLSelectElement>) => {
      onChange({
        ...values,
        status: e.target.value as GeneratedDocument['status'] | 'all',
      });
    },
    [values, onChange]
  );

  const handleTypeChange = useCallback(
    (e: React.ChangeEvent<HTMLSelectElement>) => {
      onChange({
        ...values,
        type: e.target.value as DocumentType | 'all',
      });
    },
    [values, onChange]
  );

  const handleSortChange = useCallback(
    (e: React.ChangeEvent<HTMLSelectElement>) => {
      onChange({
        ...values,
        sortBy: e.target.value as DocumentFilterValues['sortBy'],
      });
    },
    [values, onChange]
  );

  const toggleSortOrder = useCallback(() => {
    onChange({
      ...values,
      sortOrder: values.sortOrder === 'asc' ? 'desc' : 'asc',
    });
  }, [values, onChange]);

  const clearFilters = useCallback(() => {
    setSearchInput('');
    onChange({
      search: '',
      status: 'all',
      type: 'all',
      sortBy: 'updatedAt',
      sortOrder: 'desc',
    });
  }, [onChange]);

  const hasActiveFilters =
    values.search !== '' ||
    values.status !== 'all' ||
    values.type !== 'all';

  return (
    <div className="document-filters">
      <div className="document-filters__row">
        <div className="document-filters__search">
          <Input
            type="search"
            placeholder="Search documents..."
            value={searchInput}
            onChange={(e) => setSearchInput(e.target.value)}
            aria-label="Search documents"
          />
        </div>

        <div className="document-filters__selects">
          <div className="document-filters__select-group">
            <label htmlFor="status-filter" className="document-filters__label">
              Status
            </label>
            <select
              id="status-filter"
              className="document-filters__select"
              value={values.status}
              onChange={handleStatusChange}
            >
              {STATUS_OPTIONS.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
          </div>

          <div className="document-filters__select-group">
            <label htmlFor="type-filter" className="document-filters__label">
              Type
            </label>
            <select
              id="type-filter"
              className="document-filters__select"
              value={values.type}
              onChange={handleTypeChange}
            >
              {TYPE_OPTIONS.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
          </div>

          <div className="document-filters__select-group">
            <label htmlFor="sort-filter" className="document-filters__label">
              Sort By
            </label>
            <div className="document-filters__sort-wrapper">
              <select
                id="sort-filter"
                className="document-filters__select"
                value={values.sortBy}
                onChange={handleSortChange}
              >
                {SORT_OPTIONS.map((option) => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </select>
              <button
                type="button"
                className="document-filters__sort-order"
                onClick={toggleSortOrder}
                aria-label={`Sort ${values.sortOrder === 'asc' ? 'descending' : 'ascending'}`}
                title={`Sort ${values.sortOrder === 'asc' ? 'descending' : 'ascending'}`}
              >
                {values.sortOrder === 'asc' ? '↑' : '↓'}
              </button>
            </div>
          </div>
        </div>
      </div>

      <div className="document-filters__footer">
        <div className="document-filters__count">
          {filteredCount !== undefined && totalCount !== undefined ? (
            filteredCount === totalCount ? (
              <span>{totalCount} document{totalCount !== 1 ? 's' : ''}</span>
            ) : (
              <span>
                Showing {filteredCount} of {totalCount} documents
              </span>
            )
          ) : null}
        </div>

        {hasActiveFilters && (
          <button
            type="button"
            className="document-filters__clear"
            onClick={clearFilters}
          >
            Clear filters
          </button>
        )}
      </div>
    </div>
  );
}

// Default filter values
export const DEFAULT_FILTER_VALUES: DocumentFilterValues = {
  search: '',
  status: 'all',
  type: 'all',
  sortBy: 'updatedAt',
  sortOrder: 'desc',
};
