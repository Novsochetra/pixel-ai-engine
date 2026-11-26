import type { Clip } from './animate-client';

// pixel-train writes its GIFs at 16 frames a second.
const GIF_FPS = 16;
const USUAL_FPS = 8;

export const FPS_RANGE = { min: 1, max: 24 } as const;

export const frameDelay = (fps: number) => Math.round(1000 / fps);

export const nextFrame = (frame: number, count: number) => (count ? (frame + 1) % count : 0);

export const previousFrame = (frame: number, count: number) =>
  count ? (frame - 1 + count) % count : 0;

const clampFps = (fps: number) => Math.min(FPS_RANGE.max, Math.max(FPS_RANGE.min, fps));

// The sheet keeps `kept` of the clip's `used` frames, so at this speed it lasts as long as the GIF.
export function clipFps({ kept, used }: Pick<Clip, 'kept' | 'used'>) {
  if (!kept || !used) {
    return USUAL_FPS;
  }

  return clampFps(Math.round((kept * GIF_FPS) / used));
}

// The frames sit side by side, so a sheet that does not say how many it keeps is cut into squares.
export function frameCount(sheetWidth: number, sheetHeight: number, kept: number) {
  if (kept > 0) {
    return kept;
  }

  return sheetHeight ? Math.max(1, Math.round(sheetWidth / sheetHeight)) : 1;
}

export interface FrameBox {
  width: number;
  height: number;
  offset: number;
}

// The window shows one frame at the scale; the sheet behind it slides a frame's width per step.
export function frameBox(sheet: { width: number; height: number }, count: number, frame: number) {
  const width = sheet.width / count;

  return (scale: number): FrameBox => ({
    width: width * scale,
    height: sheet.height * scale,
    offset: -frame * width * scale,
  });
}

export const frameText = (frame: number, count: number) => `Frame ${frame + 1} of ${count}`;
