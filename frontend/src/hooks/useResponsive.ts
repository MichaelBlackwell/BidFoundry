/**
 * Responsive Utilities Hook (F12 - Polish)
 *
 * Provides utilities for handling responsive behavior.
 * Integrates with the AccessibilityProvider for viewport detection.
 */

import { useState, useEffect, useCallback } from 'react';
import { useUIStore } from '../stores/uiStore';

// ============================================================================
// Types
// ============================================================================

export interface Breakpoints {
  mobile: number;
  tablet: number;
  desktop: number;
}

export interface ViewportInfo {
  width: number;
  height: number;
  isMobile: boolean;
  isTablet: boolean;
  isDesktop: boolean;
  orientation: 'portrait' | 'landscape';
}

// ============================================================================
// Default Breakpoints
// ============================================================================

export const DEFAULT_BREAKPOINTS: Breakpoints = {
  mobile: 768,
  tablet: 1280,
  desktop: 1920,
};

// ============================================================================
// Hook: useViewport
// ============================================================================

export function useViewport(breakpoints: Breakpoints = DEFAULT_BREAKPOINTS): ViewportInfo {
  const [viewport, setViewport] = useState<ViewportInfo>(() => getViewportInfo(breakpoints));

  useEffect(() => {
    let timeoutId: ReturnType<typeof setTimeout>;

    const handleResize = () => {
      clearTimeout(timeoutId);
      timeoutId = setTimeout(() => {
        setViewport(getViewportInfo(breakpoints));
      }, 100);
    };

    window.addEventListener('resize', handleResize);
    window.addEventListener('orientationchange', handleResize);

    return () => {
      window.removeEventListener('resize', handleResize);
      window.removeEventListener('orientationchange', handleResize);
      clearTimeout(timeoutId);
    };
  }, [breakpoints]);

  return viewport;
}

function getViewportInfo(breakpoints: Breakpoints): ViewportInfo {
  const width = window.innerWidth;
  const height = window.innerHeight;

  return {
    width,
    height,
    isMobile: width < breakpoints.mobile,
    isTablet: width >= breakpoints.mobile && width < breakpoints.tablet,
    isDesktop: width >= breakpoints.tablet,
    orientation: width > height ? 'landscape' : 'portrait',
  };
}

// ============================================================================
// Hook: useMediaQuery
// ============================================================================

export function useMediaQuery(query: string): boolean {
  const [matches, setMatches] = useState<boolean>(() => {
    if (typeof window === 'undefined') return false;
    return window.matchMedia(query).matches;
  });

  useEffect(() => {
    const mediaQuery = window.matchMedia(query);

    const handleChange = (e: MediaQueryListEvent) => {
      setMatches(e.matches);
    };

    // Initial check
    setMatches(mediaQuery.matches);

    // Listen for changes
    mediaQuery.addEventListener('change', handleChange);
    return () => {
      mediaQuery.removeEventListener('change', handleChange);
    };
  }, [query]);

  return matches;
}

// ============================================================================
// Hook: usePrefersDarkMode
// ============================================================================

export function usePrefersDarkMode(): boolean {
  return useMediaQuery('(prefers-color-scheme: dark)');
}

// ============================================================================
// Hook: usePrefersReducedMotion
// ============================================================================

export function usePrefersReducedMotion(): boolean {
  return useMediaQuery('(prefers-reduced-motion: reduce)');
}

// ============================================================================
// Hook: usePrefersReducedTransparency
// ============================================================================

export function usePrefersReducedTransparency(): boolean {
  return useMediaQuery('(prefers-reduced-transparency: reduce)');
}

// ============================================================================
// Hook: useBreakpoint
// ============================================================================

export type BreakpointName = 'mobile' | 'tablet' | 'desktop';

export function useBreakpoint(breakpoints: Breakpoints = DEFAULT_BREAKPOINTS): BreakpointName {
  const { isMobile, isTablet } = useViewport(breakpoints);

  if (isMobile) return 'mobile';
  if (isTablet) return 'tablet';
  return 'desktop';
}

// ============================================================================
// Hook: useResponsiveValue
// ============================================================================

export function useResponsiveValue<T>(values: {
  mobile?: T;
  tablet?: T;
  desktop: T;
}): T {
  const breakpoint = useBreakpoint();

  switch (breakpoint) {
    case 'mobile':
      return values.mobile ?? values.tablet ?? values.desktop;
    case 'tablet':
      return values.tablet ?? values.desktop;
    default:
      return values.desktop;
  }
}

// ============================================================================
// Hook: useSidebarBehavior
// ============================================================================

export interface SidebarBehavior {
  shouldAutoCollapse: boolean;
  isOverlay: boolean;
  defaultCollapsed: boolean;
}

export function useSidebarBehavior(): SidebarBehavior {
  const { isMobile, isTablet } = useUIStore();

  return {
    shouldAutoCollapse: isMobile || isTablet,
    isOverlay: isTablet,
    defaultCollapsed: isMobile || isTablet,
  };
}

// ============================================================================
// Hook: useLayoutMode
// ============================================================================

export type LayoutMode = 'split' | 'stacked' | 'single';

export function useLayoutMode(): LayoutMode {
  const breakpoint = useBreakpoint();

  switch (breakpoint) {
    case 'mobile':
      return 'single';
    case 'tablet':
      return 'stacked';
    default:
      return 'split';
  }
}

export default useViewport;
