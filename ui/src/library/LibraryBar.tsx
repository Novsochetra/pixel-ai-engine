import { Picker } from '@/components/picker/Picker';
import { SearchField } from '@/components/search-field/SearchField';
import { Segmented } from '@/components/segmented/Segmented';
import type { LibraryRequest } from './use-library';
import type { LibraryFilter, LibraryPicker } from './library-view';

const FILTERS = [
  { value: 'all', label: 'All' },
  { value: 'flagged', label: 'Flagged' },
  { value: 'exports', label: 'Exports' },
  { value: 'tryouts', label: 'Try-outs' },
] as const;

interface LibraryBarProps {
  request: LibraryRequest;
  picker: LibraryPicker | null;
  onFilter: (filter: LibraryFilter) => void;
  onSearch: (search: string) => void;
  onChoice: (choice: string) => void;
}

export function LibraryBar({ request, picker, onFilter, onSearch, onChoice }: LibraryBarProps) {
  const searchLabel = request.filter === 'all' ? 'Search characters' : 'Search';

  return (
    <div className="library-bar">
      <div className="library-bar__filter">
        <Segmented label="Show" options={FILTERS} value={request.filter} onChange={onFilter} />
      </div>
      <SearchField label={searchLabel} value={request.search} onChange={onSearch} />
      {picker ? (
        <Picker
          label={picker.label}
          value={picker.value}
          options={picker.options}
          onChange={onChoice}
        />
      ) : null}
    </div>
  );
}
