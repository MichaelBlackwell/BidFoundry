import type { CompanyProfile } from '../../types';
import {
  naicsCodesToStrings,
  certificationsToStrings,
  pastPerformanceToStrings,
} from '../../api/profiles';
import { Button } from '../ui';
import './ProfileCard.css';

interface ProfileCardProps {
  profile: CompanyProfile;
  onEdit: (profile: CompanyProfile) => void;
  onDelete: (profile: CompanyProfile) => void;
}

export function ProfileCard({ profile, onEdit, onDelete }: ProfileCardProps) {
  const formatDate = (date: Date) => {
    return new Intl.DateTimeFormat('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
    }).format(new Date(date));
  };

  // Extract display strings from structured types
  const naicsCodes = naicsCodesToStrings(profile.naicsCodes);
  const certifications = certificationsToStrings(profile.certifications);
  const pastPerformance = pastPerformanceToStrings(profile.pastPerformance);

  return (
    <div className="profile-card">
      <div className="profile-card__header">
        <h3 className="profile-card__name">{profile.name}</h3>
        <div className="profile-card__actions">
          <Button variant="ghost" size="sm" onClick={() => onEdit(profile)}>
            Edit
          </Button>
          <Button variant="ghost" size="sm" onClick={() => onDelete(profile)}>
            Delete
          </Button>
        </div>
      </div>

      {profile.description && (
        <p className="profile-card__description">{profile.description}</p>
      )}

      <div className="profile-card__details">
        {naicsCodes.length > 0 && (
          <div className="profile-card__detail">
            <span className="profile-card__detail-label">NAICS Codes</span>
            <div className="profile-card__tags">
              {naicsCodes.map((code) => (
                <span key={code} className="profile-card__tag">
                  {code}
                </span>
              ))}
            </div>
          </div>
        )}

        {certifications.length > 0 && (
          <div className="profile-card__detail">
            <span className="profile-card__detail-label">Certifications</span>
            <div className="profile-card__tags">
              {certifications.map((cert) => (
                <span key={cert} className="profile-card__tag profile-card__tag--cert">
                  {cert}
                </span>
              ))}
            </div>
          </div>
        )}

        {pastPerformance.length > 0 && (
          <div className="profile-card__detail">
            <span className="profile-card__detail-label">Past Performance</span>
            <ul className="profile-card__list">
              {pastPerformance.slice(0, 3).map((pp, i) => (
                <li key={i}>{pp}</li>
              ))}
              {pastPerformance.length > 3 && (
                <li className="profile-card__more">
                  +{pastPerformance.length - 3} more
                </li>
              )}
            </ul>
          </div>
        )}
      </div>

      <div className="profile-card__footer">
        <span className="profile-card__date">Updated {formatDate(profile.updatedAt)}</span>
      </div>
    </div>
  );
}
