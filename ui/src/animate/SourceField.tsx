import { Picker } from '@/components/picker/Picker';
import { Segmented } from '@/components/segmented/Segmented';
import { PixelImage } from '@/library/PixelImage';
import type { AnimateSources, UploadLimits } from './animate-client';
import { findMade, type SourceKind } from './animate-form';
import { UploadButton } from './UploadButton';
import type { SourcePicker } from './use-source-picker';

const KINDS: { value: SourceKind; label: string }[] = [
  { value: 'made', label: 'Generated' },
  { value: 'upload', label: 'Uploaded' },
];

const EMPTY = {
  made: 'No characters yet. Make one in Create, or upload a PNG.',
  upload: 'No PNG uploaded yet.',
};

function previewOf(sources: AnimateSources, source: string, view: string | undefined) {
  const made = findMade(sources, source);

  if (made) {
    const shown = view ?? made.views[0]!;

    return { src: made.pictures[shown]!, alt: `${made.subject}, ${shown}` };
  }

  const upload = sources.uploads.find((entry) => entry.value === source);

  return upload ? { src: upload.src, alt: upload.label } : null;
}

interface SourceFieldProps {
  picker: SourcePicker;
  limits: UploadLimits;
  sources: AnimateSources;
  source: string;
  view: string | undefined;
}

// What to work on: a character made in Create, shown in one of its views, or a PNG of your own.
export function SourceField({ picker, limits, sources, source, view }: SourceFieldProps) {
  const list = picker.kind === 'made' ? sources.characters : sources.uploads;
  const preview = previewOf(sources, source, view);

  return (
    <div className="form-field">
      <span className="form-field__label" aria-hidden="true">
        Character
      </span>
      <Segmented
        label="Character"
        options={KINDS}
        value={picker.kind}
        onChange={picker.chooseKind}
      />
      {list.length ? (
        <Picker
          label={picker.kind === 'made' ? 'Generated character' : 'Uploaded picture'}
          value={source}
          options={list}
          isStacked
          onChange={picker.chooseSource}
        />
      ) : (
        <p className="form-note">{EMPTY[picker.kind]}</p>
      )}
      {preview ? (
        <span className="source-preview pixel-art">
          <PixelImage key={preview.src} src={preview.src} alt={preview.alt} />
        </span>
      ) : null}
      {picker.kind === 'upload' ? <UploadButton upload={picker.upload} limits={limits} /> : null}
    </div>
  );
}
