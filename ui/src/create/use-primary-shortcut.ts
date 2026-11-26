import { useEffect, useEffectEvent } from 'react';
import { useIsTopScreen } from '@/navigation/stack/layer-context';

const isPrimaryShortcut = (event: KeyboardEvent) =>
  event.key === 'Enter' && (event.metaKey || event.ctrlKey);

// ⌘↩ runs the screen's one primary action, from the form or from anywhere on the page.
export function usePrimaryShortcut(run: () => void) {
  const isTop = useIsTopScreen();

  const onKey = useEffectEvent((event: KeyboardEvent) => {
    if (isTop && isPrimaryShortcut(event)) {
      event.preventDefault();
      run();
    }
  });

  useEffect(() => {
    window.addEventListener('keydown', onKey);

    return () => window.removeEventListener('keydown', onKey);
  }, []);
}
