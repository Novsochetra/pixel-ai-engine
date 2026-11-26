import { getJson, postJson } from '@/api/read-json';
import type { Choice } from '@/create/create-client';
import type { JobView } from '@/jobs/jobs-client';
import type { Point } from './loss-chart';

export type Task = 'rotate' | 'create';

export interface Run {
  name: string;
  task: Task;
  createdAt: string;
  model: string;
  size: number | null;
  export: string;
  sources: string[];
  moreExports: string[];
  step: number;
  steps: number;
  secondsPerStep: number | null;
  passes: number | null;
  checkpoints: string[];
  final: boolean;
  loss: Point[];
  val: Point[];
  tryouts: Choice[];
  isTraining: boolean;
}

export interface ExportSource {
  name: string;
  licence: string;
  use: string;
  count: number | null;
}

export interface TrainingExport {
  name: string;
  sources: ExportSource[];
}

export interface TrainingOptions {
  tasks: Choice[];
  models: Choice[];
  sizes: Choice[];
  exports: TrainingExport[];
  namePattern: string;
  mostSteps: number;
  characters: { min: number; max: number; default: number };
  defaults: {
    task: Task;
    model: string;
    size: string;
    steps: number;
    tryoutModel: string;
    addSteps: number;
  };
}

export interface StartBody {
  name: string;
  task: Task;
  export: string;
  model: string;
  size: string;
  steps: number;
  sources: string[];
  moreExports: string[];
  repeat: Record<string, number>;
}

export interface ResumeBody {
  run: string;
  steps: number;
}

export interface TryoutBody {
  run: string;
  checkpoint: string;
  model: string;
  characters: number;
}

export const fetchRuns = () => getJson<{ runs: Run[] }>('/api/runs');

export const fetchTrainingOptions = () => getJson<TrainingOptions>('/api/training/options');

export const postStart = (body: StartBody) => postJson<JobView>('/api/training/start', body);

export const postResume = (body: ResumeBody) => postJson<JobView>('/api/training/resume', body);

export const postTryout = (body: TryoutBody) => postJson<JobView>('/api/training/tryout', body);
