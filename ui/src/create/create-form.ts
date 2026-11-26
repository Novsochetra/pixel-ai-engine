import type { Choice, Facing, FormOptions, GenerateBody } from './create-client';

export type CreateValues = GenerateBody;

export const STANDING = 'standing';

export function defaultValues(options: FormOptions, rotateLoras: readonly Choice[]): CreateValues {
  const { defaults } = options;

  return {
    prompt: '',
    pose: '',
    facing: defaults.facing,
    characters: options.characters.default,
    sprite: defaults.sprite,
    drawWith: '',
    drawingModel: defaults.model,
    turnWith: rotateLoras[0]?.value ?? '',
    turningModel: defaults.model,
  };
}

const isStanding = (pose: string) => {
  const words = pose.trim().toLowerCase();

  return words === '' || words === STANDING;
};

// The same refusals as the server's, said before Generate rather than after it.
export function drawWithNote({ facing, pose }: Pick<CreateValues, 'facing' | 'pose'>) {
  if (facing === 'side') {
    return 'A create LoRA draws only front views, so a side view is drawn with none.';
  }

  if (!isStanding(pose)) {
    return 'A create LoRA draws only standing sprites, so this pose is drawn with none.';
  }

  return null;
}

export const turnWithNote = (facing: Facing) =>
  facing === 'side' ? 'A side view is flipped for the left, not turned.' : null;

export const isReady = (values: CreateValues) => values.prompt.trim() !== '';

// A choice the form shows as off is sent as none, so the server never refuses it.
export function createBody(values: CreateValues): GenerateBody {
  return {
    ...values,
    prompt: values.prompt.trim(),
    pose: values.pose.trim(),
    drawWith: drawWithNote(values) ? '' : values.drawWith,
    turnWith: turnWithNote(values.facing) ? '' : values.turnWith,
  };
}
