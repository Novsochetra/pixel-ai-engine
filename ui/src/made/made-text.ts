import type { MadeTarget } from './made-client';

const UNDO_NOTE = 'It goes to the trash, and you can undo it right after.';

// A turned character shares its folder with the rest of its Create set, so all of it goes.
function charactersText(count: number | null): string {
  if (count === null) {
    return ' and every character made with it, in Create and Rotate';
  }

  return count > 1 ? ` and the ${count} characters made with it` : '';
}

const clipsText = (count: number | null) => (count && count > 1 ? ` and its ${count} clips` : '');

// Deleting removes the whole folder, so the question says how much goes with it.
export function deleteQuestion({ kind, title, count }: MadeTarget): string {
  if (kind === 'animated') {
    return `Delete the animation of “${title}”${clipsText(count)}? ${UNDO_NOTE}`;
  }

  return `Delete “${title}”${charactersText(count)}? ${UNDO_NOTE}`;
}

export const deletedText = (title: string) => `Deleted “${title}”.`;
