import type { ExportSource, StartBody, TrainingExport, TrainingOptions } from './training-client';

type Values = StartBody;
type Repeat = Record<string, number>;

// A fixed half of a big source, or a small one shown more often so it is not lost.
export const REPEATS = [0.5, 1, 2, 5, 10] as const;

export const findExport = (options: TrainingOptions, name: string): TrainingExport | null =>
  options.exports.find((entry) => entry.name === name) ?? null;

export const exportSources = (options: TrainingOptions, name: string) =>
  (findExport(options, name)?.sources ?? []).map((source) => source.name);

// pixel-train takes more exports for a create run only.
export const moreExportsOf = (values: Values) =>
  values.task === 'create' ? values.moreExports : [];

export const otherExports = (options: TrainingOptions, values: Values) =>
  options.exports.filter((entry) => entry.name !== values.export);

export function formSources(options: TrainingOptions, values: Values): ExportSource[] {
  return [values.export, ...moreExportsOf(values)].flatMap(
    (name) => findExport(options, name)?.sources ?? [],
  );
}

// An added export comes with all its sources checked, and taking it away takes them too.
export function toggleExport(options: TrainingOptions, values: Values, name: string) {
  const own = exportSources(options, values.export);
  const added = exportSources(options, name).filter((source) => !own.includes(source));

  if (values.moreExports.includes(name)) {
    return {
      moreExports: values.moreExports.filter((other) => other !== name),
      sources: values.sources.filter((source) => !added.includes(source)),
    };
  }

  return { moreExports: [...values.moreExports, name], sources: [...values.sources, ...added] };
}

export function setRepeat(repeat: Repeat, source: string, times: number): Repeat {
  const rest = Object.fromEntries(Object.entries(repeat).filter(([name]) => name !== source));

  return times === 1 ? rest : { ...rest, [source]: times };
}

// What the run trains on: the sources of an export taken away, or a repeat of a source left
// unchecked, stay in the form for later but are not sent.
export function sentData(options: TrainingOptions, values: Values) {
  const names = formSources(options, values).map((source) => source.name);
  const sources = values.sources.filter((source) => names.includes(source));
  const repeat = Object.fromEntries(
    Object.entries(values.repeat).filter(([source]) => sources.includes(source)),
  );

  return { moreExports: moreExportsOf(values), sources, repeat };
}

export function charactersText(sources: readonly ExportSource[]) {
  if (sources.some((source) => source.count === null)) {
    return sources.map((source) => source.name).join(', ');
  }

  const total = sources.reduce((sum, source) => sum + (source.count ?? 0), 0);

  return `${total.toLocaleString('en-US')} characters`;
}
