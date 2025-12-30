/**
 * StreamingContent Component
 *
 * Displays text content that may be streaming in real-time.
 * Includes a blinking cursor when actively streaming.
 * Optimized for performance with memoization.
 */

import { memo, useCallback, useEffect, useMemo, useRef, useState } from 'react';
import './StreamingContent.css';

interface StreamingContentProps {
  /** The text content to display */
  content: string;
  /** Whether content is currently streaming */
  isStreaming?: boolean;
  /** Maximum height before scrolling (in pixels) */
  maxHeight?: number;
  /** Whether to auto-scroll to bottom as content streams */
  autoScroll?: boolean;
  /** Whether to enable collapsible truncation for long content */
  collapsible?: boolean;
  /** Maximum character length before truncation (default: 200) */
  maxLength?: number;
  /** Additional CSS class name */
  className?: string;
}

export const StreamingContent = memo(function StreamingContent({
  content,
  isStreaming = false,
  maxHeight,
  autoScroll = true,
  collapsible = true,
  maxLength = 200,
  className = '',
}: StreamingContentProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const contentEndRef = useRef<HTMLSpanElement>(null);
  const [isExpanded, setIsExpanded] = useState(false);

  // Auto-scroll to bottom when content changes (if enabled)
  useEffect(() => {
    if (autoScroll && isStreaming && contentEndRef.current) {
      contentEndRef.current.scrollIntoView({ behavior: 'smooth', block: 'end' });
    }
  }, [content, isStreaming, autoScroll]);

  // Toggle expansion
  const toggleExpanded = useCallback((e: React.MouseEvent) => {
    e.stopPropagation();
    setIsExpanded((prev) => !prev);
  }, []);

  // Compute display content and whether truncation is needed
  const hasLongContent = collapsible && !isStreaming && content.length > maxLength;
  const displayContent = useMemo(() => {
    if (isStreaming || isExpanded || content.length <= maxLength) {
      return content;
    }
    return content.substring(0, maxLength) + '...';
  }, [content, isStreaming, isExpanded, maxLength]);

  // Handle empty content
  if (!content && !isStreaming) {
    return null;
  }

  return (
    <div
      ref={containerRef}
      className={`streaming-content ${isStreaming ? 'streaming-content--active' : ''} ${className}`}
      style={maxHeight ? { maxHeight: `${maxHeight}px` } : undefined}
      aria-live={isStreaming ? 'polite' : undefined}
      aria-atomic={isStreaming ? 'false' : undefined}
    >
      <div className="streaming-content__text">
        {displayContent}
        {isStreaming && (
          <>
            <span
              className="streaming-content__cursor"
              aria-hidden="true"
            />
            <span ref={contentEndRef} className="streaming-content__scroll-anchor" />
          </>
        )}
      </div>
      {hasLongContent && (
        <button
          type="button"
          className="streaming-content__expand-btn"
          onClick={toggleExpanded}
          aria-expanded={isExpanded}
        >
          {isExpanded ? 'Show less' : 'Show more'}
        </button>
      )}
    </div>
  );
});

export default StreamingContent;
