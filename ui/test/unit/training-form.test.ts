import { describe, expect, it } from 'vitest';
import { primaryPlan, type PlanState } from '@/training/primary-plan';
import {
  addedSteps,
  passesText,
  resumeTarget,
  runFacts,
  runSubtitle,
  sourcesText,
  stepShare,
  timeLeftText,
} from '@/training/run-view';
import {
  addStepsTarget,
  modeOf,
  resumeProblem,
  tryoutDefaults,
  tryoutProblem,
} from '@/training/training-actions';
import {
  defaultValues,
  isNonCommercial,
  newRunProblem,
  nonCommercialSources,
  startBody,
  toggleSource,
} from '@/training/training-form';
import { CREATE_RUN, OPTIONS, ROTATE_RUN } from '../integration/training-server';

const UNFINISHED = { ...ROTATE_RUN, step: 1500, steps: 2000 };

describe('the new run form', () => {
  it('starts on the first export with all its sources checked', () => {
    expect(defaultValues(OPTIONS)).toEqual({
      name: '',
      task: 'rotate',
      export: 'characters-v2',
      model: 'flux2-klein-base-4b',
      size: '256',
      steps: 2000,
      sources: ['lpc-4view', 'pac'],
      moreExports: [],
      repeat: {},
    });
  });

  it('keeps the sources in the export order', () => {
    const order = ['lpc-4view', 'pac', 'pixellab'];

    expect(toggleSource(['pixellab'], 'lpc-4view', order)).toEqual(['lpc-4view', 'pixellab']);
    expect(toggleSource(['lpc-4view', 'pac'], 'lpc-4view', order)).toEqual(['pac']);
  });

  it('knows a non-commercial licence, short or written out', () => {
    expect(isNonCommercial('CC-BY-NC-4.0')).toBe(true);
    expect(isNonCommercial('PixelLab output: local use only, no commercial app')).toBe(true);
    expect(isNonCommercial('CC-BY-SA-3.0')).toBe(false);
    expect(isNonCommercial('NCSA')).toBe(false);
    expect(nonCommercialSources(OPTIONS, defaultValues(OPTIONS))).toEqual(['pac']);
  });

  it('checks the form as train_job does', () => {
    const good = { ...defaultValues(OPTIONS), name: ' rotate-v3 ' };
    const runs = [ROTATE_RUN];

    expect(newRunProblem(good, OPTIONS, runs)).toBeNull();
    expect(newRunProblem({ ...good, name: 'a b' }, OPTIONS, runs)).toMatch(/^Name the run/);
    expect(newRunProblem({ ...good, name: 'rotate-v2' }, OPTIONS, runs)).toMatch(
      /^There is already/,
    );
    expect(newRunProblem({ ...good, sources: [] }, OPTIONS, runs)).toBe(
      'Pick at least one source.',
    );
    expect(newRunProblem({ ...good, steps: NaN }, OPTIONS, runs)).toBe(
      'Steps must be a whole number from 1 to 50,000.',
    );
    expect(startBody(good, OPTIONS).name).toBe('rotate-v3');
  });
});

describe('a run', () => {
  it('reads as its task, model and size', () => {
    expect(runSubtitle(ROTATE_RUN, OPTIONS.models)).toBe('rotate · base · 256 px');
    expect(sourcesText(ROTATE_RUN)).toBe('all sources');
    expect(sourcesText(CREATE_RUN)).toBe('lpc-4view, pac, opengameart-v1');
  });

  it('says how far it is and how long is left', () => {
    expect(stepShare(UNFINISHED)).toBe(0.75);
    expect(timeLeftText(UNFINISHED)).toBe('about 3.8 h left');
    expect(timeLeftText(ROTATE_RUN)).toBe('');
  });

  it('says how much of the data it has seen', () => {
    expect(passesText(null)).toBe('');
    expect(passesText(0.4249)).toBe('42% of the data seen');
    expect(passesText(1.26)).toBe('the data seen 1.3 times');
  });

  it('lists its details, and a final when it has one', () => {
    const facts = runFacts(ROTATE_RUN, OPTIONS.models);

    expect(facts.find((fact) => fact.label === 'Val loss')?.value).toBe('0.0805');
    expect(facts.at(-1)).toEqual({ label: 'Final', value: 'saved' });
  });
});

describe('the run actions', () => {
  it('resumes an unfinished run to its plan, a finished one by the steps to add', () => {
    expect(resumeTarget(UNFINISHED, 500)).toBe(2000);
    expect(resumeTarget(ROTATE_RUN, 500)).toBe(2500);
    expect(addStepsTarget(UNFINISHED, 500)).toBe(2000);
    expect(addedSteps(ROTATE_RUN, 2300)).toBe(300);
  });

  it('resumes only past the last step', () => {
    expect(resumeProblem(ROTATE_RUN, 2000, OPTIONS)).toBe(
      'Steps must be a whole number from 2,001 to 50,000.',
    );
    expect(resumeProblem(ROTATE_RUN, 2001, OPTIONS)).toBeNull();
  });

  it('tries a rotate run only, with its first checkpoint', () => {
    const values = tryoutDefaults(ROTATE_RUN, OPTIONS);

    expect(values).toEqual({
      checkpoint: 'runs/rotate-v2/final',
      model: 'flux2-klein-4b',
      characters: 4,
    });
    expect(tryoutProblem(ROTATE_RUN, values)).toBeNull();
    expect(tryoutProblem(CREATE_RUN, values)).toBe('Try a create run on the Create screen.');
    expect(tryoutProblem(ROTATE_RUN, { ...values, checkpoint: '' })).toMatch(/no checkpoint/);
  });

  it('follows the selection with the primary action', () => {
    expect(modeOf(null, 'tryout')).toBe('new');
    expect(modeOf(ROTATE_RUN, 'tryout')).toBe('tryout');
    expect(modeOf(CREATE_RUN, 'tryout')).toBe('resume');
  });

  it('waits for the form before it sends', () => {
    const state: PlanState = {
      options: undefined,
      runs: undefined,
      newRun: null,
      run: null,
      target: NaN,
      tryout: null,
    };

    expect(primaryPlan('new', state)).toEqual({
      problem: 'The form is still loading.',
      post: null,
    });
    expect(
      primaryPlan('resume', { ...state, options: OPTIONS, run: ROTATE_RUN, target: 2500 }).problem,
    ).toBeNull();
  });
});
