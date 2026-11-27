import { getJson, postJson } from '@/api/read-json';
import type { UploadLimits, UploadSource } from '@/animate/animate-client';
import type { JobView } from '@/jobs/jobs-client';
import type { Picture } from '@/library/library-client';

export interface Choice {
  value: string;
  label: string;
}

// A LoRA comes with the model it learnt on, which it draws best with. A create LoRA also names
// the views it learnt to draw.
export interface LoraChoice extends Choice {
  model: string;
  views?: Facing[];
}

export interface FormOptions extends UploadLimits {
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
  reference: string;
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
  reference: string;
}

export type LoraTask = 'create' | 'rotate';

export const fetchFormOptions = () => getJson<FormOptions>('/api/generate/options');

export const fetchLoras = (task: LoraTask) =>
  getJson<{ loras: LoraChoice[] }>(`/api/loras?task=${task}`).then((reply) => reply.loras);

export const fetchUploads = () =>
  getJson<{ uploads: UploadSource[] }>('/api/uploads').then((reply) => reply.uploads);

export const fetchGenerated = () => getJson<{ items: GeneratedEntry[] }>('/api/generated');

export const postGenerate = (body: GenerateBody) => postJson<JobView>('/api/generate', body);
