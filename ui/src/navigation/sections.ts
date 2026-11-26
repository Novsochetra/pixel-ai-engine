import type { IconName } from '@/components/icons';

export type SectionGroup = 'make' | 'data';

export interface Section {
  id: string;
  title: string;
  path: string;
  group: SectionGroup;
  icon: IconName;
  summary: string;
  inTabBar: boolean;
}

export const GROUPS: readonly { id: SectionGroup; title: string }[] = [
  { id: 'make', title: 'Make' },
  { id: 'data', title: 'Data' },
];

// A narrow screen's tab bar holds four sections and More, as the HIG allows five tabs at most.
export const SECTIONS: readonly Section[] = [
  {
    id: 'create',
    title: 'Create',
    path: '/create',
    group: 'make',
    icon: 'create',
    summary: 'Make a character from a few words.',
    inTabBar: true,
  },
  {
    id: 'rotate',
    title: 'Rotate',
    path: '/rotate',
    group: 'make',
    icon: 'rotate',
    summary: 'Turn a character to 4 or 8 directions.',
    inTabBar: false,
  },
  {
    id: 'animate',
    title: 'Animate',
    path: '/animate',
    group: 'make',
    icon: 'animate',
    summary: 'Give a character an action, as a sprite sheet.',
    inTabBar: true,
  },
  {
    id: 'landscape',
    title: 'Landscape',
    path: '/landscape',
    group: 'make',
    icon: 'landscape',
    summary: 'Make a background from a few words.',
    inTabBar: false,
  },
  {
    id: 'library',
    title: 'Library',
    path: '/library',
    group: 'data',
    icon: 'library',
    summary: 'Look through the dataset, flagged images and exports.',
    inTabBar: true,
  },
  {
    id: 'training',
    title: 'Training',
    path: '/training',
    group: 'data',
    icon: 'training',
    summary: 'Train models and compare their runs.',
    inTabBar: true,
  },
];

export const sectionsIn = (group: SectionGroup) =>
  SECTIONS.filter((section) => section.group === group);

export const tabSections = () => SECTIONS.filter((section) => section.inTabBar);

export const moreSections = () => SECTIONS.filter((section) => !section.inTabBar);

export function sectionAt(pathname: string): Section | undefined {
  return SECTIONS.find(
    (section) => pathname === section.path || pathname.startsWith(`${section.path}/`),
  );
}
