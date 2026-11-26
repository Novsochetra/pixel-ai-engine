import { useCurrentJob } from '@/jobs/use-current-job';
import { createBody, isReady } from './create-form';
import { useGenerate } from './use-create';
import { useCreateForm } from './use-create-form';
import { usePrimaryShortcut } from './use-primary-shortcut';

export function useCreateScreen() {
  const form = useCreateForm();
  const generate = useGenerate();
  const isBusy = useCurrentJob().data?.job?.status === 'running';
  const isFilled = form.values !== null && isReady(form.values);

  const run = () => {
    if (form.values && isFilled && !isBusy && !generate.isPending) {
      generate.mutate(createBody(form.values));
    }
  };

  usePrimaryShortcut(run);

  return {
    form,
    run,
    button: {
      notReady: isFilled ? null : 'Write what to draw first.',
      isBusy,
      isStarting: generate.isPending,
    },
    error: generate.error?.message ?? null,
    closeError: generate.reset,
  };
}
