import type {
  CharacterDetail,
  CharacterEntry,
  CharacterImage,
  CharacterPage,
} from './library-client';
import {
  countText,
  NO_MATCHES,
  type Fact,
  type LibraryItem,
  type LibraryView,
} from './library-view';

const NOT_IMPORTED = {
  title: 'Nothing imported yet',
  text: 'Import a source, then come back. In dataset/, run',
  command: 'uv run pixel import pac lpc-4view',
};

const viewCount = (count: number) => (count === 1 ? '1 view' : `${count} views`);

export function characterItem(entry: CharacterEntry): LibraryItem {
  return {
    key: entry.id,
    title: entry.id,
    subtitle: entry.caption || viewCount(entry.views.length),
    pictures: entry.views,
    character: entry.id,
    facts: [
      { label: 'Source', value: entry.source },
      { label: 'Views', value: entry.views.map((view) => view.label).join(', ') },
    ],
  };
}

function sourcePicker(page: CharacterPage, source: string) {
  const options = page.sources.map((name) => ({ value: name, label: name }));

  return { label: 'Source', value: source, options: [{ value: '', label: 'All' }, ...options] };
}

export function characterView(page: CharacterPage, source: string): LibraryView {
  const items = page.characters.map(characterItem);

  return {
    sections: items.length ? [{ title: '', items }] : [],
    page: page.page,
    pages: page.pages,
    hasMore: page.page < page.pages,
    empty: page.imported ? NO_MATCHES : NOT_IMPORTED,
    picker: page.imported ? sourcePicker(page, source) : null,
    summary: [{ title: 'Dataset', facts: [{ label: 'Characters', value: countText(page.total) }] }],
  };
}

function analysisFacts(image: CharacterImage): Fact[] {
  const { analysis } = image;

  if (!analysis) {
    return [{ label: 'Status', value: 'Not analyzed yet' }];
  }

  return [
    { label: 'Status', value: analysis.status },
    { label: 'Flags', value: analysis.flags.join(', ') || 'None' },
    { label: 'Colors', value: countText(analysis.colors) },
    { label: 'Drawn at', value: `${analysis.scale}×` },
  ];
}

export function imageFacts(image: CharacterImage): Fact[] {
  return [
    { label: 'Size', value: `${image.width} × ${image.height}` },
    { label: 'License', value: image.license },
    { label: 'Use', value: image.use },
    ...analysisFacts(image),
    { label: 'File', value: image.file },
  ];
}

export function groupText(group: CharacterDetail['group']): string {
  if (!group) {
    return '';
  }

  if (group.kind === 'copy') {
    return `Exact copy of ${group.characters[0]}, so it is dropped.`;
  }

  return `Near-identical group, kept together in the split: ${group.characters.join(', ')}.`;
}
