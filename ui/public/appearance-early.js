// A classic script in the page's head, run before anything is drawn, so a light screen never shows
// dark first. It makes the same choice as resolveAppearance in src/appearance/appearance.ts.
{
  const root = document.documentElement;
  const system = window.matchMedia?.('(prefers-color-scheme: light)').matches ? 'light' : 'dark';
  const readSaved = () => {
    try {
      return JSON.parse(window.localStorage.getItem('pixel.appearance'));
    } catch {
      return null;
    }
  };
  const saved = readSaved();
  const isKept = saved && saved.system === system && ['light', 'dark'].includes(saved.choice);
  root.dataset.appearance = isKept ? saved.choice : system;
}
