import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import type { OutputTab } from '../types';

export interface DocumentTab {
  id: string;
  label: string;
  path: string;
}

interface UIState {
  // Sidebar
  sidebarCollapsed: boolean;
  toggleSidebar: () => void;
  setSidebarCollapsed: (collapsed: boolean) => void;

  // Active document tabs
  documentTabs: DocumentTab[];
  addDocumentTab: (tab: DocumentTab) => void;
  removeDocumentTab: (id: string) => void;
  clearDocumentTabs: () => void;

  // Debate theater layout
  debateTheaterWidth: number;
  setDebateTheaterWidth: (width: number) => void;

  // Preview pane
  previewExpanded: boolean;
  togglePreviewExpanded: () => void;
  setPreviewExpanded: (expanded: boolean) => void;

  // Auto-scroll for streaming content
  autoScrollEnabled: boolean;
  toggleAutoScroll: () => void;
  setAutoScrollEnabled: (enabled: boolean) => void;

  // Output tabs
  activeTab: OutputTab;
  setActiveTab: (tab: OutputTab) => void;

  // Keyboard shortcuts help modal
  shortcutHelpOpen: boolean;
  setShortcutHelpOpen: (open: boolean) => void;

  // Accessibility
  reducedMotion: boolean;
  setReducedMotion: (reduced: boolean) => void;

  // Responsive
  isMobile: boolean;
  isTablet: boolean;
  setViewport: (isMobile: boolean, isTablet: boolean) => void;
}

export const useUIStore = create<UIState>()(
  persist(
    (set) => ({
      // Sidebar
      sidebarCollapsed: false,
      toggleSidebar: () =>
        set((state) => ({ sidebarCollapsed: !state.sidebarCollapsed })),
      setSidebarCollapsed: (collapsed) => set({ sidebarCollapsed: collapsed }),

      // Active document tabs
      documentTabs: [],
      addDocumentTab: (tab) =>
        set((state) => {
          // Don't add duplicate tabs
          if (state.documentTabs.some((t) => t.id === tab.id)) {
            return state;
          }
          return { documentTabs: [...state.documentTabs, tab] };
        }),
      removeDocumentTab: (id) =>
        set((state) => ({
          documentTabs: state.documentTabs.filter((t) => t.id !== id),
        })),
      clearDocumentTabs: () => set({ documentTabs: [] }),

      // Debate theater layout
      debateTheaterWidth: 50, // percentage
      setDebateTheaterWidth: (width) =>
        set({ debateTheaterWidth: Math.max(30, Math.min(70, width)) }),

      // Preview pane
      previewExpanded: false,
      togglePreviewExpanded: () =>
        set((state) => ({ previewExpanded: !state.previewExpanded })),
      setPreviewExpanded: (expanded) => set({ previewExpanded: expanded }),

      // Auto-scroll for streaming content
      autoScrollEnabled: true,
      toggleAutoScroll: () =>
        set((state) => ({ autoScrollEnabled: !state.autoScrollEnabled })),
      setAutoScrollEnabled: (enabled) => set({ autoScrollEnabled: enabled }),

      // Output tabs
      activeTab: 'document',
      setActiveTab: (tab) => set({ activeTab: tab }),

      // Keyboard shortcuts help modal
      shortcutHelpOpen: false,
      setShortcutHelpOpen: (open) => set({ shortcutHelpOpen: open }),

      // Accessibility
      reducedMotion: false,
      setReducedMotion: (reduced) => set({ reducedMotion: reduced }),

      // Responsive
      isMobile: false,
      isTablet: false,
      setViewport: (isMobile, isTablet) => set({ isMobile, isTablet }),
    }),
    {
      name: 'ui-storage',
      partialize: (state) => ({
        sidebarCollapsed: state.sidebarCollapsed,
        debateTheaterWidth: state.debateTheaterWidth,
        reducedMotion: state.reducedMotion,
      }),
    }
  )
);
