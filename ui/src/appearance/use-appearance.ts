import { useState } from 'react';
import { APPEARANCE_KEY, otherAppearance, systemAppearance, type Appearance } from './appearance';

function readRoot(): Appearance {
  return document.documentElement.dataset.appearance === 'light' ? 'light' : 'dark';
}

export function useAppearance() {
  const [appearance, setAppearance] = useState<Appearance>(readRoot);

  const toggle = () => {
    const choice = otherAppearance(appearance);
    const saved = { choice, system: systemAppearance(window) };

    document.documentElement.dataset.appearance = choice;
    window.localStorage.setItem(APPEARANCE_KEY, JSON.stringify(saved));
    setAppearance(choice);
  };

  return { appearance, toggle };
}
