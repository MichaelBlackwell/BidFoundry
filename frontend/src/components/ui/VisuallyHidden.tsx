/**
 * Visually Hidden Component (F12 - Accessibility)
 *
 * Hides content visually while keeping it accessible to screen readers.
 * Use for labels, announcements, or additional context for assistive technology.
 */

import type { ReactNode, HTMLAttributes } from 'react';
import './VisuallyHidden.css';

interface VisuallyHiddenProps extends HTMLAttributes<HTMLSpanElement> {
  children: ReactNode;
  as?: 'span' | 'div' | 'h1' | 'h2' | 'h3' | 'h4' | 'h5' | 'h6' | 'p';
}

export function VisuallyHidden({
  children,
  as: Component = 'span',
  className = '',
  ...props
}: VisuallyHiddenProps) {
  return (
    <Component className={`sr-only ${className}`.trim()} {...props}>
      {children}
    </Component>
  );
}

export default VisuallyHidden;
