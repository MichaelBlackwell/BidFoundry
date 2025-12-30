/**
 * Responsive Container Component (F12 - Responsive)
 *
 * Provides responsive layout utilities for handling different viewport sizes.
 * Shows/hides content or renders alternatives based on breakpoints.
 */

import type { ReactNode } from 'react';
import { useAccessibility } from '../../providers';

// ============================================================================
// ResponsiveContainer - Show/hide based on viewport
// ============================================================================

interface ResponsiveContainerProps {
  children: ReactNode;
  showOnMobile?: boolean;
  showOnTablet?: boolean;
  showOnDesktop?: boolean;
}

export function ResponsiveContainer({
  children,
  showOnMobile = true,
  showOnTablet = true,
  showOnDesktop = true,
}: ResponsiveContainerProps) {
  const { isMobile, isTablet, isDesktop } = useAccessibility();

  if (isMobile && !showOnMobile) return null;
  if (isTablet && !showOnTablet) return null;
  if (isDesktop && !showOnDesktop) return null;

  return <>{children}</>;
}

// ============================================================================
// MobileOnly - Only show on mobile
// ============================================================================

interface MobileOnlyProps {
  children: ReactNode;
}

export function MobileOnly({ children }: MobileOnlyProps) {
  return (
    <ResponsiveContainer showOnMobile showOnTablet={false} showOnDesktop={false}>
      {children}
    </ResponsiveContainer>
  );
}

// ============================================================================
// TabletUp - Show on tablet and desktop
// ============================================================================

interface TabletUpProps {
  children: ReactNode;
}

export function TabletUp({ children }: TabletUpProps) {
  return (
    <ResponsiveContainer showOnMobile={false} showOnTablet showOnDesktop>
      {children}
    </ResponsiveContainer>
  );
}

// ============================================================================
// DesktopOnly - Only show on desktop
// ============================================================================

interface DesktopOnlyProps {
  children: ReactNode;
}

export function DesktopOnly({ children }: DesktopOnlyProps) {
  return (
    <ResponsiveContainer showOnMobile={false} showOnTablet={false} showOnDesktop>
      {children}
    </ResponsiveContainer>
  );
}

// ============================================================================
// ResponsiveSwitch - Render different content based on viewport
// ============================================================================

interface ResponsiveSwitchProps {
  mobile?: ReactNode;
  tablet?: ReactNode;
  desktop?: ReactNode;
  fallback?: ReactNode;
}

export function ResponsiveSwitch({
  mobile,
  tablet,
  desktop,
  fallback = null,
}: ResponsiveSwitchProps) {
  const { isMobile, isTablet, isDesktop } = useAccessibility();

  if (isMobile && mobile !== undefined) return <>{mobile}</>;
  if (isTablet && tablet !== undefined) return <>{tablet}</>;
  if (isDesktop && desktop !== undefined) return <>{desktop}</>;

  return <>{fallback}</>;
}

// ============================================================================
// MobileMessage - Show generation-disabled message on mobile
// ============================================================================

interface MobileGenerationDisabledProps {
  className?: string;
}

export function MobileGenerationDisabled({
  className = '',
}: MobileGenerationDisabledProps) {
  const { isMobile } = useAccessibility();

  if (!isMobile) return null;

  return (
    <div className={`mobile-generation-disabled ${className}`.trim()}>
      <div className="mobile-generation-disabled__icon">
        <svg
          xmlns="http://www.w3.org/2000/svg"
          width="48"
          height="48"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="1.5"
          strokeLinecap="round"
          strokeLinejoin="round"
        >
          <rect x="2" y="3" width="20" height="14" rx="2" ry="2" />
          <line x1="8" y1="21" x2="16" y2="21" />
          <line x1="12" y1="17" x2="12" y2="21" />
        </svg>
      </div>
      <h2 className="mobile-generation-disabled__title">
        Desktop Required
      </h2>
      <p className="mobile-generation-disabled__message">
        Document generation requires a desktop browser for the best experience.
        You can view completed documents on mobile.
      </p>
    </div>
  );
}

export default ResponsiveContainer;
