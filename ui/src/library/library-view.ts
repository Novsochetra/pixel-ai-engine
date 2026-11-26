import type { Picture } from './library-client';

export type LibraryFilter = 'all' | 'flagged' | 'exports' | 'tryouts';

export interface Fact {
  label: string;
  value: string;
}

export interface LibraryItem {
  key: string;
  title: string;
  subtitle: string;
  pictures: Picture[];
  character: string | null;
  facts: Fact[];
  // Set for what Create and Rotate made: the folder under data/generated/ it can be deleted as.
  made?: { folder: string; characters: number | null };
}

export interface LibrarySection {
  title: string;
  items: LibraryItem[];
}

export interface LibraryNotice {
  title: string;
  text: string;
  command?: string;
}

export interface LibraryPicker {
  label: string;
  value: string;
  options: { value: string; label: string }[];
}

export interface LibrarySummary {
  title: string;
  facts: Fact[];
}

export interface LibraryView {
  sections: LibrarySection[];
  page: number;
  pages: number | null;
  hasMore: boolean;
  empty: LibraryNotice;
  picker: LibraryPicker | null;
  summary: LibrarySummary[];
}

export const NO_MATCHES: LibraryNotice = {
  title: 'No matches',
  text: 'Try other words, or clear the search.',
};

export const countText = (count: number) => count.toLocaleString('en-US');

export const dateText = (stamp: string) =>
  new Date(stamp).toLocaleString('en-US', { dateStyle: 'medium', timeStyle: 'short' });

export function listText(counts: Record<string, number>): string {
  const parts = Object.entries(counts).map(([name, count]) => `${name} ${countText(count)}`);

  return parts.join(' · ') || 'None';
}

export function singlePage(sections: LibrarySection[], empty: LibraryNotice) {
  return { sections: sections.filter((section) => section.items.length), page: 1, empty };
}

const holds = (text: string, words: string) => text.toLowerCase().includes(words);

function matches(item: LibraryItem, section: LibrarySection, words: string): boolean {
  return [item.title, item.subtitle, section.title].some((text) => holds(text, words));
}

// The server searches the whole dataset; the shorter lists are searched here, as they come whole.
export function searchView(view: LibraryView, search: string): LibraryView {
  const words = search.trim().toLowerCase();

  if (!words) {
    return view;
  }

  const sections = view.sections
    .map((section) => ({
      ...section,
      items: section.items.filter((item) => matches(item, section, words)),
    }))
    .filter((section) => section.items.length);

  return { ...view, sections, empty: NO_MATCHES };
}
