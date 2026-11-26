import { useId, useRef, type ReactNode } from 'react';
import { Icon } from '@/components/icons';
import { useSheet } from './use-sheet';
import './sheet.css';
import './sheet-phone.css';

interface SheetProps {
  title: string;
  // A compact sheet holds one short question and its answers, as the HIG's alert-sized sheet.
  size?: 'regular' | 'compact';
  isOpen: boolean;
  onClosed: () => void;
  children: ReactNode;
}

// iPadOS's form sheet: centered on wide screens, rising from the bottom on narrow ones, where a
// finger can pull it down (sheet-gesture.js).
export function Sheet({ title, size = 'regular', isOpen, onClosed, children }: SheetProps) {
  const dialog = useRef<HTMLDialogElement>(null);
  const closeButton = useRef<HTMLButtonElement>(null);
  const titleId = useId();

  useSheet({ dialog, closeButton }, isOpen, onClosed);

  return (
    <dialog className={`sheet sheet--${size}`} ref={dialog} aria-labelledby={titleId} tabIndex={-1}>
      <header className="sheet__header">
        <h2 className="sheet__title" id={titleId}>
          {title}
        </h2>
        <button className="glass-button" type="button" aria-label="Close" ref={closeButton}>
          <Icon name="close" />
        </button>
      </header>
      <div className="sheet__body">{children}</div>
    </dialog>
  );
}
