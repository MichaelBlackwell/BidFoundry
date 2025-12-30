/**
 * Accessibility Provider (F12 - Polish)
 *
 * Provides accessibility features including:
 * - Screen reader live announcements
 * - Reduced motion preference detection
 * - Viewport size detection for responsive layout
 * - Focus management utilities
 */

import {
  createContext,
  useContext,
  useEffect,
  useCallback,
  useRef,
  type ReactNode,
} from 'react';
import { useUIStore } from '../stores/uiStore';

// ============================================================================
// Types
// ============================================================================

export type AnnouncementPoliteness = 'polite' | 'assertive';

export interface AccessibilityContextValue {
  announce: (message: string, politeness?: AnnouncementPoliteness) => void;
  reducedMotion: boolean;
  isMobile: boolean;
  isTablet: boolean;
  isDesktop: boolean;
  focusTrap: (container: HTMLElement | null, enabled?: boolean) => () => void;
}

// ============================================================================
// Context
// ============================================================================

const AccessibilityContext = createContext<AccessibilityContextValue | null>(null);

// ============================================================================
// Hook
// ============================================================================

export function useAccessibility(): AccessibilityContextValue {
  const context = useContext(AccessibilityContext);
  if (!context) {
    throw new Error('useAccessibility must be used within AccessibilityProvider');
  }
  return context;
}

// Convenience hook for just announcements
export function useAnnounce(): (message: string, politeness?: AnnouncementPoliteness) => void {
  const { announce } = useAccessibility();
  return announce;
}

// ============================================================================
// Provider Component
// ============================================================================

interface AccessibilityProviderProps {
  children: ReactNode;
}

export function AccessibilityProvider({ children }: AccessibilityProviderProps) {
  const { setReducedMotion, setViewport, reducedMotion, isMobile, isTablet } =
    useUIStore();

  // Refs for live regions
  const politeRef = useRef<HTMLDivElement>(null);
  const assertiveRef = useRef<HTMLDivElement>(null);
  const announceTimeoutRef = useRef<ReturnType<typeof setTimeout>>();

  // Announce to screen readers
  const announce = useCallback(
    (message: string, politeness: AnnouncementPoliteness = 'polite') => {
      const region = politeness === 'assertive' ? assertiveRef.current : politeRef.current;
      if (!region) return;

      // Clear any pending announcement
      if (announceTimeoutRef.current) {
        clearTimeout(announceTimeoutRef.current);
      }

      // Clear the region first to ensure the new message is announced
      region.textContent = '';

      // Set the new message after a brief delay to ensure it's picked up
      announceTimeoutRef.current = setTimeout(() => {
        region.textContent = message;
      }, 50);
    },
    []
  );

  // Detect reduced motion preference
  useEffect(() => {
    const mediaQuery = window.matchMedia('(prefers-reduced-motion: reduce)');

    const handleChange = (e: MediaQueryListEvent | MediaQueryList) => {
      setReducedMotion(e.matches);
    };

    // Initial check
    handleChange(mediaQuery);

    // Listen for changes
    mediaQuery.addEventListener('change', handleChange);
    return () => {
      mediaQuery.removeEventListener('change', handleChange);
    };
  }, [setReducedMotion]);

  // Detect viewport size for responsive layout
  useEffect(() => {
    const MOBILE_BREAKPOINT = 768;
    const TABLET_BREAKPOINT = 1280;

    const handleResize = () => {
      const width = window.innerWidth;
      const newIsMobile = width < MOBILE_BREAKPOINT;
      const newIsTablet = width >= MOBILE_BREAKPOINT && width < TABLET_BREAKPOINT;
      setViewport(newIsMobile, newIsTablet);
    };

    // Initial check
    handleResize();

    // Listen for resize with debounce
    let timeoutId: ReturnType<typeof setTimeout>;
    const debouncedResize = () => {
      clearTimeout(timeoutId);
      timeoutId = setTimeout(handleResize, 100);
    };

    window.addEventListener('resize', debouncedResize);
    return () => {
      window.removeEventListener('resize', debouncedResize);
      clearTimeout(timeoutId);
    };
  }, [setViewport]);

  // Focus trap utility
  const focusTrap = useCallback(
    (container: HTMLElement | null, enabled = true): (() => void) => {
      if (!container || !enabled) return () => {};

      const focusableSelectors = [
        'button:not([disabled])',
        'a[href]',
        'input:not([disabled])',
        'select:not([disabled])',
        'textarea:not([disabled])',
        '[tabindex]:not([tabindex="-1"])',
      ].join(', ');

      const getFocusableElements = () =>
        Array.from(container.querySelectorAll<HTMLElement>(focusableSelectors));

      const handleKeyDown = (e: KeyboardEvent) => {
        if (e.key !== 'Tab') return;

        const focusableElements = getFocusableElements();
        if (focusableElements.length === 0) return;

        const firstElement = focusableElements[0];
        const lastElement = focusableElements[focusableElements.length - 1];

        if (e.shiftKey) {
          if (document.activeElement === firstElement) {
            e.preventDefault();
            lastElement.focus();
          }
        } else {
          if (document.activeElement === lastElement) {
            e.preventDefault();
            firstElement.focus();
          }
        }
      };

      container.addEventListener('keydown', handleKeyDown);
      return () => {
        container.removeEventListener('keydown', handleKeyDown);
      };
    },
    []
  );

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (announceTimeoutRef.current) {
        clearTimeout(announceTimeoutRef.current);
      }
    };
  }, []);

  const value: AccessibilityContextValue = {
    announce,
    reducedMotion,
    isMobile,
    isTablet,
    isDesktop: !isMobile && !isTablet,
    focusTrap,
  };

  return (
    <AccessibilityContext.Provider value={value}>
      {children}
      {/* Live regions for screen reader announcements */}
      <div
        ref={politeRef}
        role="status"
        aria-live="polite"
        aria-atomic="true"
        className="sr-only"
      />
      <div
        ref={assertiveRef}
        role="alert"
        aria-live="assertive"
        aria-atomic="true"
        className="sr-only"
      />
    </AccessibilityContext.Provider>
  );
}

export default AccessibilityProvider;
