import { useEffect, useRef, type RefObject } from 'react';
import { createSheet } from './sheet-controller.js';

interface SheetParts {
  dialog: RefObject<HTMLDialogElement | null>;
  closeButton: RefObject<HTMLButtonElement | null>;
}

// A sheet (sheet-controller.js) shows while isOpen holds. Escape, a click on the dimmed page and its close
// button close it with its animation, then onClosed says so.
export function useSheet(
  { dialog, closeButton }: SheetParts,
  isOpen: boolean,
  onClosed: () => void,
) {
  const sheet = useRef<ReturnType<typeof createSheet> | null>(null);
  const closed = useRef(onClosed);

  useEffect(() => {
    closed.current = onClosed;
  });

  useEffect(() => {
    const lifetime = new AbortController();
    const { signal } = lifetime;
    const parts = { dialog: dialog.current!, closeButton: closeButton.current! };
    const made = createSheet({ ...parts, document: parts.dialog.ownerDocument, signal });

    // a close fires a task later, by when React's development checks may have opened it again
    const onClose = () => !parts.dialog.open && closed.current();

    parts.dialog.addEventListener('close', onClose, { signal });
    sheet.current = made;

    return () => {
      lifetime.abort();
      made.finish();
    };
  }, [dialog, closeButton]);

  useEffect(() => {
    if (isOpen) {
      sheet.current?.open();
    } else {
      sheet.current?.close();
    }
  }, [isOpen]);
}
