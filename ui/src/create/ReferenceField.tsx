import type { UploadLimits } from '@/animate/animate-client';
import { UploadButton } from '@/animate/UploadButton';
import { Picker } from '@/components/picker/Picker';
import { PixelImage } from '@/library/PixelImage';
import { useReferenceUpload, useUploads } from './use-create';

const NONE = { value: '', label: 'None' };

interface ReferenceFieldProps {
  limits: UploadLimits;
  value: string;
  onChange: (reference: string) => void;
}

// A picture the model draws from, as well as the words. A new upload is chosen at once.
export function ReferenceField({ limits, value, onChange }: ReferenceFieldProps) {
  const uploads = useUploads().data ?? [];
  const upload = useReferenceUpload((uploaded) => onChange(uploaded.value));
  const chosen = uploads.find((entry) => entry.value === value);

  return (
    <div className="form-field">
      <Picker
        label="Reference"
        value={value}
        options={[NONE, ...uploads]}
        isStacked
        onChange={onChange}
      />
      {chosen ? (
        <span className="source-preview pixel-art">
          <PixelImage key={chosen.src} src={chosen.src} alt={`Reference: ${chosen.label}`} />
        </span>
      ) : null}
      <p className="form-note">Optional. A picture of the character, or of the look you want.</p>
      <UploadButton upload={upload} limits={limits} />
    </div>
  );
}
