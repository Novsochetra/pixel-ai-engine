import { usePrimaryShortcut } from '@/create/use-primary-shortcut';
import { useCurrentJob } from '@/jobs/use-current-job';
import { formProblem } from './animate-checks';
import { animateBody } from './animate-form';
import { useAnimate } from './use-animate';
import { useAnimateForm } from './use-animate-form';

export function useAnimateScreen() {
  const form = useAnimateForm();
  const animate = useAnimate();
  const isBusy = useCurrentJob().data?.job?.status === 'running';
  const problem = form.values && form.options ? formProblem(form.values, form.options) : null;
  const notReady = form.values ? problem : 'The form is still loading.';

  const run = () => {
    if (form.values && notReady === null && !isBusy && !animate.isPending) {
      animate.mutate(animateBody(form.values));
    }
  };

  usePrimaryShortcut(run);

  return {
    form,
    problem,
    run,
    button: { notReady, isBusy, isStarting: animate.isPending },
    error: animate.error?.message ?? null,
    closeError: animate.reset,
  };
}
