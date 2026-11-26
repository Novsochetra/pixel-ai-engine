import { getJson, postJson } from '@/api/read-json';
import type { UploadLimits } from '@/animate/animate-client';
import type { Choice } from '@/create/create-client';
import type { JobView } from '@/jobs/jobs-client';
import type { Picture } from '@/library/library-client';

export interface RotateOptions extends UploadLimits {
  models: Choice[];
  sprites: Choice[];
  views: string[];
  defaults: { sprite: string; model: string; views: string[] };
}

export interface TurnedCharacter {
  key: string;
  folder: string;
  seed: number;
  prompt: string;
  createdAt: string;
  sprite: number;
  rotatedFrom: string;
  turnWith: string;
  turningModel: string;
  views: Picture[];
}

export interface RotateBody {
  source: string;
  lora: string;
  turningModel: string;
  sprite: string;
  views: string[];
}

export const fetchRotateOptions = () => getJson<RotateOptions>('/api/rotate/options');

export const fetchRotated = () => getJson<{ characters: TurnedCharacter[] }>('/api/rotated');

export const postRotate = (body: RotateBody) => postJson<JobView>('/api/rotate', body);
