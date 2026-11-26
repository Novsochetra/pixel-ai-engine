import { describe, expect, it } from 'vitest';
import { characterView, groupText, imageFacts } from '@/library/character-view';
import { flaggedView } from '@/library/collection-view';
import { tryoutsView } from '@/library/tryout-view';
import type { CharacterImage, CharacterPage, FlaggedPage } from '@/library/library-client';
import { listText, NO_MATCHES, searchView, type LibraryView } from '@/library/library-view';

const PAGE: CharacterPage = {
  imported: true,
  characters: [
    {
      id: 'pac/train/0',
      source: 'pac',
      caption: '',
      views: [{ label: 'front', src: '/api/images/pac/train/0/front.png' }],
    },
  ],
  total: 61,
  page: 1,
  pages: 3,
  sources: ['pac', 'moss-64'],
};

const item = (title: string, subtitle = '') => ({
  key: title,
  title,
  subtitle,
  pictures: [],
  character: null,
  facts: [],
});

describe('the library views', () => {
  it('lists characters with a source picker and the pages left', () => {
    const view = characterView(PAGE, 'pac');

    expect(view.sections[0]!.items[0]!.subtitle).toBe('1 view');
    expect(view.hasMore).toBe(true);
    expect(view.picker?.value).toBe('pac');
    expect(view.picker?.options.map((option) => option.label)).toEqual(['All', 'pac', 'moss-64']);
    expect(view.summary[0]!.facts).toEqual([{ label: 'Characters', value: '61' }]);
  });

  it('says how to import when nothing is imported yet', () => {
    const view = characterView({ ...PAGE, imported: false, characters: [] }, '');

    expect(view.sections).toEqual([]);
    expect(view.empty.command).toBe('uv run pixel import pac lpc-4view');
    expect(view.picker).toBeNull();
  });

  it('says how to analyze before anything can be flagged', () => {
    const page: FlaggedPage = {
      imported: true,
      analyzed: false,
      flags: [],
      flag: '',
      page: 1,
      hasMore: false,
      images: [],
    };

    expect(flaggedView(page).empty.command).toBe('uv run pixel analyze');
  });

  it('names how each try-out model did', () => {
    const run = {
      name: 'run-1',
      createdAt: '2026-11-18T10:00:00+00:00',
      device: 'mps',
      groups: [],
      models: [
        { name: 'a', repo: '', state: 'done' as const, error: '', secondsPerImage: 12.5 },
        {
          name: 'b',
          repo: '',
          state: 'failed' as const,
          error: '401 gated',
          secondsPerImage: null,
        },
      ],
    };
    const facts = tryoutsView({ runs: [run], run }).summary[0]!.facts;

    expect(facts.slice(-2)).toEqual([
      { label: 'a', value: '12.5 s per image' },
      { label: 'b', value: 'Failed: 401 gated' },
    ]);
  });

  it('searches titles, subtitles and section titles, and drops empty sections', () => {
    const view: LibraryView = {
      ...characterView(PAGE, ''),
      sections: [
        { title: 'a knight', items: [item('one'), item('two')] },
        { title: 'a frog', items: [item('three', 'green')] },
      ],
    };

    expect(searchView(view, ' KNIGHT ').sections.map((section) => section.items.length)).toEqual([
      2,
    ]);
    expect(searchView(view, 'green').sections[0]!.items[0]!.title).toBe('three');
    expect(searchView(view, 'dragon').empty).toBe(NO_MATCHES);
    expect(searchView(view, '')).toBe(view);
  });

  it('writes counts, records and groups as plain text', () => {
    const image = {
      width: 64,
      height: 48,
      license: 'CC0',
      use: 'train',
      file: 'pac/x.tar',
      analysis: null,
    } as unknown as CharacterImage;

    expect(listText({ pac: 10898, 'lpc-4view': 45016 })).toBe('pac 10,898 · lpc-4view 45,016');
    expect(listText({})).toBe('None');
    expect(imageFacts(image)).toContainEqual({ label: 'Size', value: '64 × 48' });
    expect(imageFacts(image)).toContainEqual({ label: 'Status', value: 'Not analyzed yet' });
    expect(groupText({ kind: 'copy', characters: ['pac/test/0'] })).toBe(
      'Exact copy of pac/test/0, so it is dropped.',
    );
  });
});
