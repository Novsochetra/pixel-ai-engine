import { useRef } from 'react';
import { Icon } from '@/components/icons';
import { FormError } from '@/create/FormError';
import type { AnimateOptions } from './animate-client';
import type { AnimateForm } from './use-animate-form';

const megabytes = (bytes: number) => Math.round(bytes / 1_000_000);

// The file picker hides behind a real button, so it looks and focuses like the others.
export function UploadButton({ form, options }: { form: AnimateForm; options: AnimateOptions }) {
  const input = useRef<HTMLInputElement>(null);
  const { upload } = form;

  function send(files: FileList | null) {
    const file = files?.[0];

    if (file) {
      upload.mutate(file);
    }

    input.current!.value = '';
  }

  return (
    <div className="upload-field">
      <input
        className="visually-hidden"
        ref={input}
        type="file"
        accept="image/png"
        tabIndex={-1}
        aria-label="PNG to upload"
        onChange={(event) => send(event.target.files)}
      />
      <button
        className="pill-button pill-button--tinted"
        type="button"
        disabled={upload.isPending}
        onClick={() => input.current!.click()}
      >
        <Icon name="upload" />
        {upload.isPending ? 'Uploading…' : 'Upload a PNG'}
      </button>
      <p className="form-note">
        At most {options.largestUpload} pixels a side and {megabytes(options.uploadLimit)} MB.
      </p>
      {upload.error ? <FormError message={upload.error.message} onClose={upload.reset} /> : null}
    </div>
  );
}
