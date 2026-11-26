import { FactList } from '@/components/fact-list/FactList';
import { Progress } from '@/components/progress/Progress';
import { groupText, imageFacts } from './character-view';
import { useCharacter } from './use-library';

// Every record of one character: what the importer stored and what `pixel analyze` found.
export function CharacterRecords({ id }: { id: string }) {
  const { data, error, isPending, refetch } = useCharacter(id);

  if (isPending) {
    return <Progress value={null} label="Loading the records" />;
  }

  if (error) {
    return (
      <p className="library-note" role="alert">
        The records did not load.{' '}
        <button className="pill-button pill-button--plain" type="button" onClick={() => refetch()}>
          Try again
        </button>
      </p>
    );
  }

  const note = groupText(data.group);

  return (
    <>
      {note ? <p className="library-note">{note}</p> : null}
      {data.images.map((image) => (
        <FactList key={image.id} title={`${image.label} · ${image.id}`} facts={imageFacts(image)} />
      ))}
    </>
  );
}
