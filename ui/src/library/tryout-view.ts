import type { TryoutList, TryoutModel } from './library-client';
import { dateText, singlePage, type LibraryView } from './library-view';

const NO_TRYOUTS = {
  title: 'No try-outs yet',
  text: 'Try the models first. In training/, run',
  command: 'uv run pixel-train tryout',
};

function modelText(model: TryoutModel): string {
  if (model.state === 'failed') {
    return `Failed: ${model.error}`;
  }

  return model.state === 'pending' ? 'Not run yet' : `${model.secondsPerImage} s per image`;
}

export function tryoutsView({ runs, run }: TryoutList): LibraryView {
  const sections = (run?.groups ?? []).map((group) => ({
    title: group.title,
    items: group.pictures.map((picture) => ({
      key: picture.src,
      title: picture.label,
      subtitle: group.title,
      pictures: [picture],
      character: group.character,
      facts: [{ label: 'Run', value: run!.name }],
    })),
  }));
  const facts = run
    ? [
        { label: 'Made', value: dateText(run.createdAt) },
        { label: 'Device', value: run.device || 'Unknown' },
        ...run.models.map((model) => ({ label: model.name, value: modelText(model) })),
      ]
    : [];
  const options = runs.map(({ name }) => ({ value: name, label: name }));

  return {
    ...singlePage(sections, NO_TRYOUTS),
    pages: 1,
    hasMore: false,
    picker: run ? { label: 'Run', value: run.name, options } : null,
    summary: run ? [{ title: run.name, facts }] : [],
  };
}
