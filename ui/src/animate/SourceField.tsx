import { Picker } from '@/components/picker/Picker';
import { Segmented } from '@/components/segmented/Segmented';
import { PixelImage } from '@/library/PixelImage';
import type { AnimateOptions, AnimateSources } from './animate-client';
import { findMade, type AnimateValues, type SourceKind } from './animate-form';
import { UploadButton } from './UploadButton';
import type { AnimateForm } from './use-animate-form';

const KINDS: { value: SourceKind; label: string }[] = [
  { value: 'made', label: 'Generated' },
  { value: 'upload', label: 'Uploaded' },
];

const EMPTY = {
  made: 'No characters yet. Make one in Create, or upload a PNG.',
  upload: 'No PNG uploaded yet.',
};

function previewOf(values: AnimateValues, sources: AnimateSources) {
  const made = findMade(sources, values.source);

  if (made) {
    const view = values.views[0] ?? made.views[0]!;

    return { src: made.pictures[view]!, alt: `${made.subject}, ${view}` };
  }

  const upload = sources.uploads.find((entry) => entry.value === values.source);

  return upload ? { src: upload.src, alt: upload.label } : null;
}

interface SourceFieldProps {
  form: AnimateForm;
  options: AnimateOptions;
  sources: AnimateSources;
  values: AnimateValues;
}

// What to animate: a character made in Create, with its views, or a PNG of your own.
export function SourceField({ form, options, sources, values }: SourceFieldProps) {
  const list = form.kind === 'made' ? sources.characters : sources.uploads;
  const preview = previewOf(values, sources);

  return (
    <div className="form-field">
      <span className="form-field__label" aria-hidden="true">
        Character
      </span>
      <Segmented label="Character" options={KINDS} value={form.kind} onChange={form.chooseKind} />
      {list.length ? (
        <Picker
          label={form.kind === 'made' ? 'Generated character' : 'Uploaded picture'}
          value={values.source}
          options={list}
          isStacked
          onChange={form.chooseSource}
        />
      ) : (
        <p className="form-note">{EMPTY[form.kind]}</p>
      )}
      {preview ? (
        <span className="source-preview pixel-art">
          <PixelImage key={preview.src} src={preview.src} alt={preview.alt} />
        </span>
      ) : null}
      {form.kind === 'upload' ? <UploadButton form={form} options={options} /> : null}
    </div>
  );
}
