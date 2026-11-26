import type { CSSProperties } from 'react';
import './progress.css';

// A bar when the share done is known, Apple's activity indicator when not.
export function Progress({ value, label }: { value: number | null; label: string }) {
  if (value === null) {
    return <span className="spinner" role="progressbar" aria-label={label} />;
  }

  const percent = Math.round(value * 100);

  return (
    <span
      className="progress"
      role="progressbar"
      aria-label={label}
      aria-valuemin={0}
      aria-valuemax={100}
      aria-valuenow={percent}
      style={{ '--progress': value } as CSSProperties}
    />
  );
}
