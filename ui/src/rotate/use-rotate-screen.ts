import { usePrimaryShortcut } from '@/create/use-primary-shortcut';
import { useCurrentJob } from '@/jobs/use-current-job';
import { formProblem } from './rotate-form';
import { useRotate } from './use-rotate';
import { useRotateForm } from './use-rotate-form';

export function useRotateScreen() {
  const form = useRotateForm();
  const rotate = useRotate();
  const isBusy = useCurrentJob().data?.job?.status === 'running';
  const problem = form.values ? formProblem(form.values, form.loras) : null;
  const notReady = form.values ? problem : 'The form is still loading.';

  const run = () => {
    if (form.values && notReady === null && !isBusy && !rotate.isPending) {
      rotate.mutate(form.values);
    }
  };

  usePrimaryShortcut(run);

  return {
    form,
    problem,
    run,
    button: { notReady, isBusy, isStarting: rotate.isPending },
    error: rotate.error?.message ?? null,
    closeError: rotate.reset,
  };
}
