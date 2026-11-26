// Line icons drawn like SF Symbols: one stroke weight on a 24-unit grid.
const PATHS = {
  create:
    'M12 3.5l1.9 4.6 4.6 1.9-4.6 1.9L12 16.5l-1.9-4.6L5.5 10l4.6-1.9zM18.5 15l.8 2 2 .8-2 .8-.8 2-.8-2-2-.8 2-.8z',
  rotate: 'M19.5 12a7.5 7.5 0 0 1-13 5.1M4.5 12a7.5 7.5 0 0 1 13-5.1M17.5 3v4h-4M6.5 21v-4h4',
  animate: 'M4 5.5h16v13H4zM8 5.5v13M16 5.5v13M4 9.5h4M4 14.5h4M16 9.5h4M16 14.5h4',
  landscape: 'M3 19l5.5-8 4 5.5 3-4L21 19zM16.5 8.5a2 2 0 1 0 0-.1',
  library: 'M4 4.5h7v7H4zM13 4.5h7v7h-7zM4 13.5h7v7H4zM13 13.5h7v7h-7z',
  training: 'M4 4v16h16M7.5 15l3.5-4.5 3 2.5 5-6.5',
  more: 'M6 12h.01M12 12h.01M18 12h.01',
  close: 'M6.5 6.5l11 11M17.5 6.5l-11 11',
  sun: 'M12 8a4 4 0 1 0 0 8 4 4 0 0 0 0-8zM12 2.5v2M12 19.5v2M2.5 12h2M19.5 12h2M5.3 5.3l1.4 1.4M17.3 17.3l1.4 1.4M5.3 18.7l1.4-1.4M17.3 6.7l1.4-1.4',
  moon: 'M19.5 14.5A8 8 0 0 1 9.5 4.5a8 8 0 1 0 10 10z',
  inspector: 'M3.5 5h17v14h-17zM14.5 5v14M16.5 8.5h2M16.5 11.5h2',
} as const;

export type IconName = keyof typeof PATHS;

export function Icon({ name, size = 'normal' }: { name: IconName; size?: 'normal' | 'large' }) {
  return (
    <svg className={`icon icon--${size}`} viewBox="0 0 24 24" aria-hidden="true">
      <path d={PATHS[name]} />
    </svg>
  );
}
