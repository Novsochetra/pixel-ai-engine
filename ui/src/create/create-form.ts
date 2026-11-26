import type { Facing, FormOptions, GenerateBody, LoraChoice } from './create-client';

export type CreateValues = GenerateBody;

export const STANDING = 'standing';

export const modelFor = (loras: readonly LoraChoice[], value: string, fallback: string) =>
  loras.find((lora) => lora.value === value)?.model ?? fallback;

// The newest create LoRA draws by default, on the model it learnt on (the base model); with none
// trained yet, the server's default model draws.
export function defaultValues(
  options: FormOptions,
  createLoras: readonly LoraChoice[],
): CreateValues {
  const { defaults } = options;
  const drawWith = createLoras[0]?.value ?? '';

  return {
    prompt: '',
    pose: '',
    facing: defaults.facing,
    characters: options.characters.default,
    sprite: defaults.sprite,
    drawWith,
    drawingModel: modelFor(createLoras, drawWith, defaults.model),
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

// Create draws the character only; Rotate turns it afterwards. The server would turn it here
// too when given a rotate LoRA, so the form never sends one.
export const facingNote = (facing: Facing) =>
  facing === 'side'
    ? 'Drawn from the side, facing right. The left is its mirror.'
    : 'Drawn from the front. Turn it on Rotate once you like it.';

export const isReady = (values: CreateValues) => values.prompt.trim() !== '';

// A choice the form shows as off is sent as none, so the server never refuses it.
export function createBody(values: CreateValues): GenerateBody {
  return {
    ...values,
    prompt: values.prompt.trim(),
    pose: values.pose.trim(),
    drawWith: drawWithNote(values) ? '' : values.drawWith,
  };
}
