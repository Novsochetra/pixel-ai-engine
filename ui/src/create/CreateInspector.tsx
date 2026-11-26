import type { ReactNode } from 'react';
import { Progress } from '@/components/progress/Progress';
import { CreateForm } from './CreateForm';
import type { CreateForm as Form } from './use-create-form';

// The form, with the server's last refusal above it so it is read before the fields.
export function CreateInspector({ form, error }: { form: Form; error: ReactNode }) {
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

  if (!form.values) {
    return (
      <div className="create-inspector-state">
        <Progress value={null} label="Loading the form" />
      </div>
    );
  }

  return (
    <>
      {error}
      <CreateForm form={form} />
    </>
  );
}
