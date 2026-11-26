import type { ExportSummary, FlaggedImage, FlaggedPage } from './library-client';
import {
  countText,
  dateText,
  listText,
  singlePage,
  type LibraryItem,
  type LibraryView,
} from './library-view';

const NOT_ANALYZED = {
  title: 'Not analyzed yet',
  text: 'Check the images first. In dataset/, run',
  command: 'uv run pixel analyze',
};
const NOTHING_FLAGGED = { title: 'Nothing flagged', text: 'Every image passed the checks.' };
const NO_EXPORTS = {
  title: 'No exports yet',
  text: 'Make a training set first. In dataset/, run',
  command: 'uv run pixel export',
};

function flaggedItem(image: FlaggedImage): LibraryItem {
  return {
    key: image.src,
    title: image.character,
    subtitle: image.flags.join(', '),
    pictures: [image],
    character: image.character,
    facts: [
      { label: 'View', value: image.label || 'None' },
      { label: 'Flags', value: image.flags.join(', ') },
      { label: 'Colors', value: countText(image.colors) },
      { label: 'Pixels drawn', value: countText(image.filled) },
      { label: 'Soft pixels', value: countText(image.softEdge) },
    ],
  };
}

export function flaggedView(page: FlaggedPage): LibraryView {
  const chosen = page.flags.find((flag) => flag.name === page.flag);
  const options = page.flags.map((flag) => ({
    value: flag.name,
    label: `${flag.name} (${countText(flag.count)})`,
  }));
  const facts = chosen
    ? [
        { label: 'Means', value: chosen.meaning },
        { label: 'Images', value: countText(chosen.count) },
        { label: 'Outcome', value: chosen.outcome },
      ]
    : [];

  return {
    ...singlePage([{ title: '', items: page.images.map(flaggedItem) }], NOTHING_FLAGGED),
    page: page.page,
    pages: null,
    hasMore: page.hasMore,
    empty: page.imported && page.analyzed ? NOTHING_FLAGGED : NOT_ANALYZED,
    picker: options.length ? { label: 'Flag', value: page.flag, options } : null,
    summary: chosen ? [{ title: chosen.name, facts }] : [],
  };
}

const leakText = (isLeakFree: boolean | null) =>
  ({ true: 'Passed', false: 'A leak was found', null: 'Not run' })[String(isLeakFree)]!;

function exportSummary(summary: ExportSummary) {
  const splits = Object.entries(summary.characters).map(([split, counts]) => ({
    label: split,
    value: listText(counts),
  }));

  return {
    title: summary.name,
    facts: [
      { label: 'Made', value: dateText(summary.createdAt) },
      ...splits,
      { label: 'Leak check', value: leakText(summary.isLeakFree) },
      { label: 'Left out', value: listText(summary.leftOut) },
      { label: 'Licenses', value: Object.values(summary.licenses).join(', ') },
    ],
  };
}

function exportSection(summary: ExportSummary) {
  const items = summary.samples.map((sample) => ({
    key: `${summary.name}/${sample.character}`,
    title: sample.character,
    subtitle: sample.split,
    pictures: sample.views,
    character: sample.character,
    facts: [
      { label: 'Export', value: summary.name },
      { label: 'Split', value: sample.split },
    ],
  }));

  return { title: summary.name, items };
}

export function exportsView({ exports }: { exports: ExportSummary[] }): LibraryView {
  return {
    ...singlePage(exports.map(exportSection), NO_EXPORTS),
    pages: 1,
    hasMore: false,
    picker: null,
    summary: exports.map(exportSummary),
  };
}
