import { getJson, postJson } from '@/api/read-json';
import type { JobView } from '@/jobs/jobs-client';
import type { Picture } from '@/library/library-client';

export interface Choice {
  value: string;
  label: string;
}

// A LoRA comes with the model it learnt on, which it draws best with.
export interface LoraChoice extends Choice {
  model: string;
}

export interface FormOptions {
  models: Choice[];
  sprites: Choice[];
  facing: Choice[];
  promptLength: number;
  poseLength: number;
  characters: { min: number; max: number; default: number };
  defaults: { sprite: string; model: string; facing: Facing };
}

export type Facing = 'front' | 'side';

export interface GeneratedEntry {
  folder: string;
  prompt: string;
  createdAt: string;
  sprite: number;
  facing: Facing;
  drawWith: string;
  drawingModel: string;
  turnWith: string;
  turningModel: string;
  sheets: Picture[];
}

export interface GenerateBody {
  prompt: string;
  pose: string;
  facing: Facing;
  characters: number;
  sprite: string;
  drawWith: string;
  drawingModel: string;
}

export type LoraTask = 'create' | 'rotate';

export const fetchFormOptions = () => getJson<FormOptions>('/api/generate/options');

export const fetchLoras = (task: LoraTask) =>
  getJson<{ loras: LoraChoice[] }>(`/api/loras?task=${task}`).then((reply) => reply.loras);

export const fetchGenerated = () => getJson<{ items: GeneratedEntry[] }>('/api/generated');

export const postGenerate = (body: GenerateBody) => postJson<JobView>('/api/generate', body);
