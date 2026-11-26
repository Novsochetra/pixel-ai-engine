import type { Run, StartBody, TrainingExport, TrainingOptions } from './training-client';

export type NewRunValues = StartBody;

// "CC-BY-NC-4.0", or words such as "no commercial app" in a licence written out.
const NON_COMMERCIAL = /\bNC\b|non-?commercial|no commercial/i;

export const isNonCommercial = (licence: string) => NON_COMMERCIAL.test(licence);

export const findExport = (options: TrainingOptions, name: string): TrainingExport | null =>
  options.exports.find((entry) => entry.name === name) ?? null;

export const exportSources = (options: TrainingOptions, name: string) =>
  (findExport(options, name)?.sources ?? []).map((source) => source.name);

export function nonCommercialSources(options: TrainingOptions, values: NewRunValues): string[] {
  const sources = findExport(options, values.export)?.sources ?? [];

  return sources
    .filter((source) => values.sources.includes(source.name) && isNonCommercial(source.licence))
    .map((source) => source.name);
}

export function defaultValues(options: TrainingOptions): NewRunValues {
  const exportName = options.exports[0]?.name ?? '';
  const { defaults } = options;

  return {
    name: '',
    task: defaults.task,
    export: exportName,
    model: defaults.model,
    size: defaults.size,
    steps: defaults.steps,
    sources: exportSources(options, exportName),
  };
}

// The sources stay in the export's order, whatever order they were checked in.
export function toggleSource(chosen: readonly string[], source: string, order: readonly string[]) {
  const next = chosen.includes(source)
    ? chosen.filter((name) => name !== source)
    : [...chosen, source];

  return order.filter((name) => next.includes(name));
}

// The same checks as the server's train_job, so the toolbar says what is missing before it asks.
export function newRunProblem(
  values: NewRunValues,
  options: TrainingOptions,
  runs: readonly Run[],
): string | null {
  const name = values.name.trim();

  if (!new RegExp(options.namePattern).test(name)) {
    return 'Name the run: letters, numbers, - and _, up to 40.';
  }

  if (runs.some((run) => run.name === name)) {
    return `There is already a run called ${name}. Resume it, or pick another name.`;
  }

  if (!values.sources.length) {
    return 'Pick at least one source.';
  }

  return stepsProblem(values.steps, 1, options.mostSteps);
}

export function stepsProblem(steps: number, low: number, high: number): string | null {
  if (!Number.isInteger(steps) || steps < low || steps > high) {
    return `Steps must be a whole number from ${low.toLocaleString('en-US')} to ${high.toLocaleString('en-US')}.`;
  }

  return null;
}

export const startBody = (values: NewRunValues): StartBody => ({
  ...values,
  name: values.name.trim(),
});
