import { useState } from 'react';
import { Picker } from '@/components/picker/Picker';
import { LibraryContent } from '@/library/LibraryContent';
import type { LibraryItem } from '@/library/library-view';
import { useRotateTryouts } from './use-rotate';

// The rotate try-outs in the Library's own view, for comparing a LoRA with the real views.
export function RotateTryouts({ onOpen }: { onOpen: (item: LibraryItem) => void }) {
  const [run, setRun] = useState('');
  const query = useRotateTryouts(run);
  const picker = query.data?.picker;

  return (
    <>
      {picker ? (
        <div className="rotate-runs">
          <Picker
            label={picker.label}
            value={picker.value}
            options={picker.options}
            onChange={setRun}
          />
        </div>
      ) : null}
      <LibraryContent
        query={query}
        view={query.data}
        selectedKey={undefined}
        onSelect={onOpen}
        onOpen={onOpen}
        onPage={() => undefined}
      />
    </>
  );
}
