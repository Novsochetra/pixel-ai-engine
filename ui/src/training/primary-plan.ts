import type { JobView } from '@/jobs/jobs-client';
import {
  resumeBody,
  resumeProblem,
  tryoutBody,
  tryoutProblem,
  type Mode,
  type TryoutValues,
} from './training-actions';
import {
  postResume,
  postStart,
  postTryout,
  type Run,
  type TrainingOptions,
} from './training-client';
import { newRunProblem, startBody, type NewRunValues } from './training-form';

export interface PlanState {
  options: TrainingOptions | undefined;
  runs: readonly Run[] | undefined;
  newRun: NewRunValues | null;
  run: Run | null;
  target: number;
  tryout: TryoutValues | null;
}

// What the toolbar's one button would send now, or why it cannot yet.
export type Plan =
  { problem: string; post: null } | { problem: null; post: () => Promise<JobView> };

const LOADING: Plan = { problem: 'The form is still loading.', post: null };

const refuse = (problem: string): Plan => ({ problem, post: null });

function newRunPlan({ options, runs, newRun }: PlanState): Plan {
  if (!options || !runs || !newRun) {
    return LOADING;
  }

  const problem = newRunProblem(newRun, options, runs);

  return problem
    ? refuse(problem)
    : { problem: null, post: () => postStart(startBody(newRun, options)) };
}

function resumePlan({ options, run, target }: PlanState): Plan {
  if (!options || !run) {
    return LOADING;
  }

  const problem = resumeProblem(run, target, options);

  return problem
    ? refuse(problem)
    : { problem: null, post: () => postResume(resumeBody(run, target)) };
}

function tryoutPlan({ run, tryout }: PlanState): Plan {
  if (!run || !tryout) {
    return LOADING;
  }

  const problem = tryoutProblem(run, tryout);

  return problem
    ? refuse(problem)
    : { problem: null, post: () => postTryout(tryoutBody(run, tryout)) };
}

const PLANS: Record<Mode, (state: PlanState) => Plan> = {
  new: newRunPlan,
  resume: resumePlan,
  tryout: tryoutPlan,
};

export const primaryPlan = (mode: Mode, state: PlanState) => PLANS[mode](state);
