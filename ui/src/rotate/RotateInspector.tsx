import type { ReactNode } from 'react';
import { Progress } from '@/components/progress/Progress';
import { RotateForm } from './RotateForm';
import type { RotateForm as Form } from './use-rotate-form';

interface InspectorProps {
  form: Form;
  problem: string | null;
  error: ReactNode;
}

// The form, with the server's last refusal above it so it is read before the fields.
export function RotateInspector({ form, problem, error }: InspectorProps) {
  if (form.error) {
    return (
      <div className="create-inspector-state">
        <p className="inspector-note">The form did not load. {form.error.message}</p>
        <button className="pill-button pill-button--glass" type="button" onClick={form.retry}>
          Try again
        </button>
      </div>
    );
  }

  if (!form.values || !form.options || !form.sources) {
    return (
      <div className="create-inspector-state">
        <Progress value={null} label="Loading the form" />
      </div>
    );
  }

  return (
    <>
      {error}
      <RotateForm
        form={form}
        options={form.options}
        sources={form.sources}
        values={form.values}
        problem={problem}
      />
    </>
  );
}
