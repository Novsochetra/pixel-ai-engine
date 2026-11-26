import type { AnimateSources } from '@/animate/animate-client';
import { firstSource } from '@/animate/animate-form';
import type { LoraChoice } from '@/create/create-client';
import { modelFor } from '@/create/create-form';
import type { RotateBody, RotateOptions } from './rotate-client';

export type RotateValues = RotateBody;

// Only a character with a front view can be turned.
export const turnable = (sources: AnimateSources): AnimateSources => ({
  ...sources,
  characters: sources.characters.filter((made) => made.views.includes('front')),
});

export function defaultValues(
  options: RotateOptions,
  sources: AnimateSources,
  loras: readonly LoraChoice[],
): RotateValues {
  const { defaults } = options;
  const lora = loras[0]?.value ?? '';

  return {
    source: firstSource('made', sources) || firstSource('upload', sources),
    lora,
    turningModel: modelFor(loras, lora, defaults.model),
    sprite: defaults.sprite,
    views: defaults.views,
  };
}

// The same refusals as the server's, said before Rotate rather than after it.
export function formProblem(values: RotateValues, loras: readonly LoraChoice[]): string | null {
  if (!values.source) {
    return 'Choose a character, or upload a PNG.';
  }

  if (!loras.some((lora) => lora.value === values.lora)) {
    return 'Train a rotate LoRA first, on the Training screen.';
  }

  return values.views.length ? null : 'Pick at least one view to turn to.';
}

export function turnText(values: RotateValues) {
  const count = values.views.length;

  return `Turns the front view to ${values.views.join(', ')}: ${count} picture${count === 1 ? '' : 's'}, plus a minute or two to load the model.`;
}
