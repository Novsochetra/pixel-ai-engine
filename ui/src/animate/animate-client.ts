import { getJson, postFile, postJson } from '@/api/read-json';
import type { Choice } from '@/create/create-client';
import type { JobView } from '@/jobs/jobs-client';

export interface UploadLimits {
  largestUpload: number;
  uploadLimit: number;
}

export interface AnimateOptions extends UploadLimits {
  views: string[];
  sizes: Choice[];
  frames: Choice[];
  minutes: { size: string; frames: string; minutes: number }[];
  mostActions: number;
  longestAction: number;
  subjectLength: number;
  defaults: { size: string; frames: string; actions: string; views: string[] };
}

export interface MadeSource {
  value: string;
  label: string;
  subject: string;
  views: string[];
  pictures: Record<string, string>;
}

export interface UploadSource {
  value: string;
  label: string;
  src: string;
}

export interface AnimateSources {
  characters: MadeSource[];
  uploads: UploadSource[];
}

export interface Clip {
  id: string;
  seed: number;
  view: string | null;
  action: string;
  kept: number;
  used: number | null;
  gif: string;
  raw: string;
  sheet: string;
}

export interface AnimatedRun {
  folder: string;
  source: string;
  subject: string;
  createdAt: string;
  size: number | null;
  frames: number | null;
  openEnd: boolean;
  clips: Clip[];
}

export interface AnimateBody {
  source: string;
  subject: string;
  views: string[];
  actions: string;
  size: string;
  frames: string;
}

export const fetchAnimateOptions = () => getJson<AnimateOptions>('/api/animate/options');

export const fetchAnimateSources = () => getJson<AnimateSources>('/api/animate/sources');

export const fetchAnimated = () => getJson<{ runs: AnimatedRun[] }>('/api/animated');

export const postAnimate = (body: AnimateBody) => postJson<JobView>('/api/animate', body);

export const postUpload = (file: File) =>
  postFile<{ upload: UploadSource }>(
    `/api/uploads?name=${encodeURIComponent(file.name)}`,
    file,
  ).then((reply) => reply.upload);
