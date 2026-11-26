const UNDO_NOTE = 'It goes to the trash, and you can undo it right after.';

// Deleting removes the whole folder, so the question says how much goes with it.
export function deleteQuestion(title: string, characters: number | null): string {
  if (characters === null) {
    return `Delete “${title}” and every character made with it, in Create and Rotate? ${UNDO_NOTE}`;
  }

  if (characters > 1) {
    return `Delete “${title}” and the ${characters} characters made with it? ${UNDO_NOTE}`;
  }

  return `Delete “${title}”? ${UNDO_NOTE}`;
}

export const deletedText = (title: string) => `Deleted “${title}”.`;
