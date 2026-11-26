import type { AnimateBody, AnimateOptions, AnimateSources, MadeSource } from './animate-client';

export type AnimateValues = AnimateBody;

export type SourceKind = 'made' | 'upload';

export const sourceKind = (source: string): SourceKind =>
  source.startsWith('uploads/') ? 'upload' : 'made';

export const findMade = (sources: AnimateSources, source: string): MadeSource | null =>
  sources.characters.find((made) => made.value === source) ?? null;

export function firstSource(kind: SourceKind, sources: AnimateSources): string {
  const list = kind === 'made' ? sources.characters : sources.uploads;

  return list[0]?.value ?? '';
}

// The words a character was made from describe it; they do not fit a PNG of your own.
export function sourceDefaults(
  source: string,
  options: AnimateOptions,
  sources: AnimateSources,
): Pick<AnimateValues, 'subject' | 'views'> {
  const made = findMade(sources, source);

  if (!made) {
    return { subject: '', views: [] };
  }

  const wanted = options.defaults.views.filter((view) => made.views.includes(view));

  return { subject: made.subject, views: wanted.length ? wanted : made.views.slice(0, 1) };
}

export function defaultValues(options: AnimateOptions, sources: AnimateSources): AnimateValues {
  const source = firstSource('made', sources) || firstSource('upload', sources);
  const { defaults } = options;

  return {
    source,
    ...sourceDefaults(source, options, sources),
    actions: defaults.actions,
    size: defaults.size,
    frames: defaults.frames,
  };
}

// The same tidying as the server's: spaces closed up, each action once, whatever its case.
export function actionLines(text: string): string[] {
  const actions = new Map<string, string>();

  for (const line of text.split('\n')) {
    const action = line.split(/\s+/).filter(Boolean).join(' ');

    if (action && !actions.has(action.toLowerCase())) {
      actions.set(action.toLowerCase(), action);
    }
  }

  return [...actions.values()];
}

// The views stay in the order of the options, whatever order they were picked in.
export function toggleView(chosen: readonly string[], view: string, order: readonly string[]) {
  const next = chosen.includes(view) ? chosen.filter((name) => name !== view) : [...chosen, view];

  return order.filter((name) => next.includes(name));
}

export function animateBody(values: AnimateValues): AnimateBody {
  const isUpload = sourceKind(values.source) === 'upload';

  return {
    ...values,
    subject: values.subject.split(/\s+/).filter(Boolean).join(' '),
    views: isUpload ? [] : values.views,
    actions: actionLines(values.actions).join('\n'),
  };
}
