import type { FactRow } from '@/components/fact-list/FactList';
import type { Choice } from '@/create/create-client';
import type { Run } from './training-client';

const count = (value: number) => value.toLocaleString('en-US');

export const modelName = (models: readonly Choice[], value: string) =>
  models.find((model) => model.value === value)?.label.split(' (')[0] ?? value;

export const sourcesText = (run: Run) =>
  [...(run.sources.length ? run.sources : ['all sources']), ...run.moreExports].join(', ');

export function runSubtitle(run: Run, models: readonly Choice[]): string {
  const size = run.size ? `${run.size} px` : '';

  return [run.task, modelName(models, run.model), size].filter(Boolean).join(' · ');
}

export const stepsText = (run: Run) => `Step ${count(run.step)} of ${count(run.steps)}`;

export const stepShare = (run: Run) => (run.steps ? Math.min(1, run.step / run.steps) : 0);

export function stepTimeText(seconds: number | null): string {
  return seconds === null ? '' : `${Math.round(seconds)} s a step`;
}

export function timeLeftText(run: Run): string {
  if (run.secondsPerStep === null || run.step >= run.steps) {
    return '';
  }

  const hours = ((run.steps - run.step) * run.secondsPerStep) / 3600;

  return `about ${hours.toFixed(1)} h left`;
}

// Below one pass the share of the data says more than "0.4 times".
export function passesText(passes: number | null): string {
  if (passes === null) {
    return '';
  }

  if (passes < 1) {
    return `${Math.round(passes * 100)}% of the data seen`;
  }

  return `the data seen ${passes.toFixed(1)} times`;
}

export function lastValLoss(run: Run): string {
  const last = run.val.at(-1);

  return last ? last[1].toFixed(4) : '–';
}

export function runFacts(run: Run, models: readonly Choice[]): FactRow[] {
  const facts = [
    { label: 'Task', value: run.task },
    { label: 'Model', value: modelName(models, run.model) },
    { label: 'Size', value: run.size ? `${run.size} px` : '–' },
    { label: 'Export', value: run.export || '–' },
    { label: 'Sources', value: sourcesText(run) },
    { label: 'Steps', value: `${count(run.step)} of ${count(run.steps)}` },
    { label: 'Time a step', value: stepTimeText(run.secondsPerStep) || '–' },
    { label: 'Data seen', value: passesText(run.passes) || '–' },
    { label: 'Val loss', value: lastValLoss(run) },
    { label: 'Checkpoints', value: String(run.checkpoints.length) },
  ];

  return run.final ? [...facts, { label: 'Final', value: 'saved' }] : facts;
}

// An unfinished run goes on to its plan; a finished one takes the daily few hundred more.
export const resumeTarget = (run: Run, addSteps: number) =>
  run.step < run.steps ? run.steps : run.step + addSteps;

export const addedSteps = (run: Run, target: number) => Math.max(0, target - run.step);
