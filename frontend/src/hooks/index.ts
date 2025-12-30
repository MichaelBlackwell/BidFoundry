// Profile hooks
export {
  useProfiles,
  useProfile,
  useCreateProfile,
  useUpdateProfile,
  useDeleteProfile,
} from './useProfiles';

// Generation hooks
export {
  useGeneration,
  useDocument as useGenerationDocument,
  useDocuments as useGenerationDocuments,
  useDocumentExport,
  type UseGenerationOptions,
  type UseGenerationReturn,
} from './useGeneration';

// Document management hooks (F11 - History & Document List)
export {
  useDocuments,
  useInfiniteDocuments,
  useDocument,
  useDeleteDocument,
  useDuplicateDocument,
  useUpdateDocumentStatus,
  useExportDocument,
  usePrefetchDocument,
  useInvalidateDocuments,
  DOCUMENTS_KEY,
  DOCUMENT_KEY,
} from './useDocuments';

// WebSocket hooks
export { useSwarmWebSocket, useSwarmEvent } from './useSwarmWebSocket';

// Agent card hooks
export {
  useAgentCard,
  useAgentCardsByCategory,
  useActiveAgents,
  useAgentCardExpansion,
} from './useAgentCard';

// Debate theater hooks
export {
  useDebateTheater,
  useCritiqueFilters,
  useAgentActivity,
} from './useDebateTheater';

// Document preview hooks
export {
  useDocumentPreview,
  type UseDocumentPreviewReturn,
} from './useDocumentPreview';

// Generation view hooks
export {
  useGenerationView,
  type UseGenerationViewOptions,
  type UseGenerationViewReturn,
} from './useGenerationView';

// Human review hooks
export {
  useHumanReview,
  type UseHumanReviewOptions,
  type UseHumanReviewReturn,
} from './useHumanReview';

// Final output hooks
export { useFinalOutput } from './useFinalOutput';

// Keyboard shortcuts hooks (F12 - Polish)
export {
  useKeyboardShortcuts,
  useShortcutHelp,
  formatShortcut,
  type KeyboardShortcut,
  type ShortcutGroup,
  type UseKeyboardShortcutsOptions,
  type UseKeyboardShortcutsReturn,
} from './useKeyboardShortcuts';

// Status announcements hooks (F12 - Accessibility)
export {
  useStatusAnnouncements,
  useAnnounceMessage,
  useAnnounceAgentActivity,
  type UseStatusAnnouncementsOptions,
} from './useStatusAnnouncements';

// Responsive utilities (F12 - Polish)
export {
  useViewport,
  useMediaQuery,
  usePrefersDarkMode,
  usePrefersReducedMotion,
  usePrefersReducedTransparency,
  useBreakpoint,
  useResponsiveValue,
  useSidebarBehavior,
  useLayoutMode,
  DEFAULT_BREAKPOINTS,
  type Breakpoints,
  type ViewportInfo,
  type BreakpointName,
  type SidebarBehavior,
  type LayoutMode,
} from './useResponsive';
