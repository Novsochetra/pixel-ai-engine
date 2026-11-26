import { dateText, type Fact, type LibraryItem } from '@/library/library-view';
import type { TurnedCharacter } from './rotate-client';

const whenText = (stamp: string) => (stamp ? dateText(stamp) : 'Unknown');

export const fromText = (character: TurnedCharacter) =>
  character.rotatedFrom ? `Turned from ${character.rotatedFrom}` : 'Made and turned in Create';

export const subtitleText = (character: TurnedCharacter) =>
  `${whenText(character.createdAt)} · ${character.sprite} px · ${character.turnWith || 'Unknown LoRA'}`;

function facts(character: TurnedCharacter): Fact[] {
  return [
    { label: 'Made', value: whenText(character.createdAt) },
    { label: 'Character', value: `s${character.seed} of ${character.folder}` },
    { label: 'Source', value: fromText(character) },
    { label: 'Sprite size', value: `${character.sprite} × ${character.sprite}` },
    { label: 'Turned with', value: character.turnWith || 'Unknown' },
    { label: 'Turning model', value: character.turningModel || 'Unknown' },
  ];
}

// A turned character opens in the same viewer as the library's pictures, one view at a time.
export function turnedItem(character: TurnedCharacter): LibraryItem {
  return {
    key: character.key,
    title: character.prompt,
    subtitle: subtitleText(character),
    pictures: character.views,
    character: null,
    facts: facts(character),
    made: { folder: character.folder, characters: null },
  };
}
