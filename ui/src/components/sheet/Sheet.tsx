import { useId, useRef, type ReactNode } from 'react';
import { Icon } from '@/components/icons';
import { useSheet } from './use-sheet';
import './sheet.css';
import './sheet-phone.css';

interface SheetProps {
  title: string;
  isOpen: boolean;
  onClosed: () => void;
  children: ReactNode;
}

// iPadOS's form sheet: centered on wide screens, rising from the bottom on narrow ones, where a
// finger can pull it down (sheet-gesture.js).
export function Sheet({ title, isOpen, onClosed, children }: SheetProps) {
  const dialog = useRef<HTMLDialogElement>(null);
  const closeButton = useRef<HTMLButtonElement>(null);
  const titleId = useId();

  useSheet({ dialog, closeButton }, isOpen, onClosed);

  return (
    <dialog className="sheet" ref={dialog} aria-labelledby={titleId} tabIndex={-1}>
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
