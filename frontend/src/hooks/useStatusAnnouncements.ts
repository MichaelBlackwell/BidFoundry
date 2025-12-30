/**
 * Status Announcements Hook (F12 - Accessibility)
 *
 * Provides screen reader announcements for generation status changes.
 * Implements accessibility requirements from Section 11 of the Frontend Design Document.
 */

import { useEffect, useRef, useCallback } from 'react';
import { useAnnounce, type AnnouncementPoliteness } from '../providers';
import { useSwarmStore } from '../stores/swarmStore';
import type { Phase, CritiqueSeverity } from '../types';

// ============================================================================
// Types
// ============================================================================

export interface UseStatusAnnouncementsOptions {
  enabled?: boolean;
  announceRounds?: boolean;
  announcePhases?: boolean;
  announceAgentActivity?: boolean;
  announceConfidence?: boolean;
}

// ============================================================================
// Phase Name Mapping
// ============================================================================

function getPhaseName(phase: Phase): string {
  const names: Record<Phase, string> = {
    'blue-build': 'Blue Team Building',
    'red-attack': 'Red Team Attack',
    'blue-defense': 'Blue Team Defense',
    synthesis: 'Synthesis',
  };
  return names[phase] || phase;
}

// ============================================================================
// Main Hook
// ============================================================================

export function useStatusAnnouncements(
  options: UseStatusAnnouncementsOptions = {}
): void {
  const {
    enabled = true,
    announceRounds = true,
    announcePhases = true,
    announceAgentActivity = true,
    announceConfidence = true,
  } = options;

  const announce = useAnnounce();
  const {
    status,
    currentRound,
    totalRounds,
    currentPhase,
    confidence,
    critiques,
    agents,
    escalation,
  } = useSwarmStore();

  // Track previous values to detect changes
  const prevStatus = useRef(status);
  const prevRound = useRef(currentRound);
  const prevPhase = useRef(currentPhase);
  const prevConfidence = useRef(confidence?.overall);
  const prevCritiquesCount = useRef(critiques.length);

  // Announce function with politeness control
  const announceStatus = useCallback(
    (message: string, politeness: AnnouncementPoliteness = 'polite') => {
      if (enabled) {
        announce(message, politeness);
      }
    },
    [enabled, announce]
  );

  // Status change announcements
  useEffect(() => {
    if (status !== prevStatus.current) {
      prevStatus.current = status;

      switch (status) {
        case 'running':
          announceStatus('Document generation started.', 'assertive');
          break;
        case 'review':
          announceStatus(
            'Generation paused. Human review required.',
            'assertive'
          );
          break;
        case 'complete':
          announceStatus('Document generation complete.', 'assertive');
          break;
        case 'error':
          announceStatus(
            'Document generation failed. Please check errors.',
            'assertive'
          );
          break;
      }
    }
  }, [status, announceStatus]);

  // Round change announcements
  useEffect(() => {
    if (!announceRounds) return;

    if (currentRound !== prevRound.current && currentRound > 0) {
      prevRound.current = currentRound;
      announceStatus(`Round ${currentRound} of ${totalRounds} started.`);
    }
  }, [currentRound, totalRounds, announceRounds, announceStatus]);

  // Phase change announcements
  useEffect(() => {
    if (!announcePhases) return;

    if (currentPhase !== prevPhase.current && currentPhase) {
      prevPhase.current = currentPhase;
      const phaseName = getPhaseName(currentPhase);
      announceStatus(`Phase changed to ${phaseName}.`);
    }
  }, [currentPhase, announcePhases, announceStatus]);

  // Confidence change announcements (on significant changes)
  useEffect(() => {
    if (!announceConfidence || !confidence?.overall) return;

    const currentConfidence = confidence.overall;
    const previous = prevConfidence.current;

    // Only announce if there's a significant change (5% or more)
    if (
      previous !== undefined &&
      Math.abs(currentConfidence - previous) >= 5
    ) {
      const direction = currentConfidence > previous ? 'increased' : 'decreased';
      announceStatus(
        `Document confidence ${direction} to ${currentConfidence}%.`
      );
    }

    prevConfidence.current = currentConfidence;
  }, [confidence?.overall, announceConfidence, announceStatus]);

  // New critique announcements
  useEffect(() => {
    if (!announceAgentActivity) return;

    const currentCount = critiques.length;
    const previousCount = prevCritiquesCount.current;

    if (currentCount > previousCount) {
      const newCritiques = critiques.slice(previousCount);
      const criticalCount = newCritiques.filter(
        (c) => c.severity === 'critical'
      ).length;

      if (criticalCount > 0) {
        announceStatus(
          `${criticalCount} critical critique${criticalCount > 1 ? 's' : ''} received.`,
          'assertive'
        );
      } else {
        const count = currentCount - previousCount;
        announceStatus(`${count} new critique${count > 1 ? 's' : ''} received.`);
      }
    }

    prevCritiquesCount.current = currentCount;
  }, [critiques.length, critiques, announceAgentActivity, announceStatus]);

  // Escalation announcements
  useEffect(() => {
    if (escalation && status === 'review') {
      const reasons = escalation.reasons?.join(', ') || 'consensus not reached';
      announceStatus(
        `Human review triggered: ${reasons}. Please review the document.`,
        'assertive'
      );
    }
  }, [escalation, status, announceStatus]);
}

// ============================================================================
// Individual Announcement Hooks
// ============================================================================

/**
 * Hook to announce a specific message
 */
export function useAnnounceMessage(): (
  message: string,
  politeness?: AnnouncementPoliteness
) => void {
  const announce = useAnnounce();
  return useCallback(
    (message: string, politeness: AnnouncementPoliteness = 'polite') => {
      announce(message, politeness);
    },
    [announce]
  );
}

/**
 * Hook to announce agent activity
 */
export function useAnnounceAgentActivity(): {
  announceAgentThinking: (agentName: string) => void;
  announceAgentComplete: (agentName: string) => void;
  announceCritique: (severity: CritiqueSeverity, agentName: string) => void;
} {
  const announce = useAnnounce();

  const announceAgentThinking = useCallback(
    (agentName: string) => {
      announce(`${agentName} is analyzing.`);
    },
    [announce]
  );

  const announceAgentComplete = useCallback(
    (agentName: string) => {
      announce(`${agentName} has completed.`);
    },
    [announce]
  );

  const announceCritique = useCallback(
    (severity: CritiqueSeverity, agentName: string) => {
      const politeness: AnnouncementPoliteness =
        severity === 'critical' ? 'assertive' : 'polite';
      announce(`${severity} critique from ${agentName}.`, politeness);
    },
    [announce]
  );

  return {
    announceAgentThinking,
    announceAgentComplete,
    announceCritique,
  };
}

export default useStatusAnnouncements;
