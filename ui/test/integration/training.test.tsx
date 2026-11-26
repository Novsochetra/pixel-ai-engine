import { cleanup, screen, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { RUNNING, renderApp } from './render-app';
import { postedBody, ROTATE_RUN, startState, trainingServer } from './training-server';

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
});

const inspector = () => screen.getByRole('complementary', { name: 'Inspector' });

const toolbar = () => document.querySelector<HTMLElement>('.toolbar')!;

const primary = () => within(toolbar()).getAllByRole('button')[0] as HTMLButtonElement;

const field = (label: string | RegExp) => within(inspector()).getByLabelText(label);

async function screenLoaded() {
  await within(inspector()).findByLabelText('Name');
  await screen.findByRole('list', { name: 'Training runs' });
}

async function chooseRun(name: string) {
  const cards = screen.getByRole('list', { name: 'Training runs' });

  await userEvent.click(within(cards).getByRole('button', { name: new RegExp(`^${name}`) }));
}

describe('the new run form', () => {
  it('posts the name, task, export, sources, model, size and steps', async () => {
    const server = trainingServer(startState());
    renderApp('/training', server);
    await screenLoaded();

    expect(primary().textContent).toBe('Start training');
    await userEvent.type(field('Name'), 'rotate-v3');
    await userEvent.click(within(inspector()).getByRole('button', { name: 'Create' }));
    await userEvent.click(field(/^pac/));
    await userEvent.selectOptions(field('Size'), '512');
    await userEvent.clear(field('Steps'));
    await userEvent.type(field('Steps'), '400');
    await userEvent.click(primary());

    await vi.waitFor(() => expect(postedBody(server, '/api/training/start')).toBeDefined());
    expect(postedBody(server, '/api/training/start')).toEqual({
      name: 'rotate-v3',
      task: 'create',
      export: 'characters-v2',
      model: 'flux2-klein-base-4b',
      size: '512',
      steps: 400,
      sources: ['lpc-4view'],
      moreExports: [],
      repeat: {},
    });
  });

  it('adds another export to a create run and shows a small source more often', async () => {
    const server = trainingServer(startState());
    renderApp('/training', server);
    await screenLoaded();

    expect((field('Name') as HTMLInputElement).placeholder).toBe('pixie-turn-v1');
    expect(within(inspector()).queryByLabelText(/^opengameart-v1/)).toBeNull();
    await userEvent.click(within(inspector()).getByRole('button', { name: 'Create' }));
    expect((field('Name') as HTMLInputElement).placeholder).toBe('pixie-draw-v1');
    await userEvent.type(field('Name'), 'pixie-draw-v2');
    await userEvent.click(field(/^opengameart-v1/));
    await userEvent.selectOptions(field('Times to show opengameart-2d'), '5');
    await userEvent.click(primary());

    await vi.waitFor(() => expect(postedBody(server, '/api/training/start')).toBeDefined());
    expect(postedBody(server, '/api/training/start')).toMatchObject({
      name: 'pixie-draw-v2',
      task: 'create',
      sources: ['lpc-4view', 'pac', 'opengameart-2d'],
      moreExports: ['opengameart-v1'],
      repeat: { 'opengameart-2d': 5 },
    });
  });

  it('trains on the base model, with no model to pick', async () => {
    renderApp('/training', trainingServer(startState()));
    await screenLoaded();

    expect(within(inspector()).queryByLabelText('Model')).toBeNull();
    expect(within(inspector()).getByText(/^Trains on the base model/)).toBeTruthy();
    expect(field(/^lpc-4view/).closest('label')?.textContent).toContain('45,016 characters');
  });

  it('says a non-commercial source makes the run non-commercial', async () => {
    renderApp('/training', trainingServer(startState()));
    await screenLoaded();

    expect(within(inspector()).getByRole('status').textContent).toMatch(
      /^pac has a non-commercial/,
    );

    await userEvent.click(field(/^pac/));

    expect(within(inspector()).queryByRole('status')).toBeNull();
  });

  it('checks every source of another export', async () => {
    const server = trainingServer(startState());
    renderApp('/training', server);
    await screenLoaded();

    await userEvent.selectOptions(field('Export'), 'opengameart-v1');

    expect((field(/^opengameart-2d/) as HTMLInputElement).checked).toBe(true);
  });

  it('says what is missing before Start training', async () => {
    const server = trainingServer(startState());
    renderApp('/training', server);
    await screenLoaded();

    expect(primary().disabled).toBe(true);
    expect(within(inspector()).getByText(/^Name the run/)).toBeTruthy();

    await userEvent.type(field('Name'), 'rotate-v2');
    expect(primary().title).toBe(
      'There is already a run called rotate-v2. Resume it, or pick another name.',
    );

    await userEvent.keyboard('{Meta>}{Enter}{/Meta}');
    expect(postedBody(server, '/api/training/start')).toBeUndefined();
  });

  it('shows a refused form in words', async () => {
    const detail = 'Pick a export from the list.';
    renderApp('/training', trainingServer({ ...startState(), refusal: { status: 400, detail } }));
    await screenLoaded();

    await userEvent.type(field('Name'), 'rotate-v3');
    await userEvent.keyboard('{Meta>}{Enter}{/Meta}');

    expect((await within(inspector()).findByRole('alert')).textContent).toContain(detail);
  });
});

describe('a selected run', () => {
  it('resumes to the last step and the steps added', async () => {
    const server = trainingServer(startState());
    renderApp('/training', server);
    await screenLoaded();

    await chooseRun('rotate-v2');
    expect(primary().textContent).toBe('Resume');
    expect((field('Train to step') as HTMLInputElement).value).toBe('2500');

    await userEvent.clear(field('Steps to add'));
    await userEvent.type(field('Steps to add'), '200');
    expect((field('Train to step') as HTMLInputElement).value).toBe('2200');

    await userEvent.click(within(inspector()).getByRole('button', { name: 'Add 500 steps' }));
    await userEvent.click(primary());

    await vi.waitFor(() =>
      expect(postedBody(server, '/api/training/resume')).toEqual({ run: 'rotate-v2', steps: 2500 }),
    );
  });

  it('tries out a checkpoint of a rotate run', async () => {
    const server = trainingServer(startState());
    renderApp('/training', server);
    await screenLoaded();

    await chooseRun('rotate-v2');
    await userEvent.click(within(inspector()).getByRole('button', { name: 'Try out' }));
    expect(primary().textContent).toBe('Try out');

    await userEvent.selectOptions(field('Checkpoint'), ROTATE_RUN.tryouts[1]!.value);
    await userEvent.click(
      within(inspector()).getByRole('button', { name: 'Test characters: one more' }),
    );
    await userEvent.keyboard('{Meta>}{Enter}{/Meta}');

    await vi.waitFor(() =>
      expect(postedBody(server, '/api/training/tryout')).toEqual({
        run: 'rotate-v2',
        checkpoint: 'runs/rotate-v2/checkpoints/step-002000',
        model: 'flux2-klein-4b',
        characters: 5,
      }),
    );
  });

  it('sends a create run to Create to be tried', async () => {
    renderApp('/training', trainingServer(startState()));
    await screenLoaded();

    await chooseRun('pixie-draw-v1');

    expect(within(inspector()).queryByRole('button', { name: 'Try out' })).toBeNull();
    expect(within(inspector()).getByRole('link', { name: 'Create' }).getAttribute('href')).toBe(
      '/create',
    );
    expect(primary().textContent).toBe('Resume');
  });

  it('goes back to a new run', async () => {
    renderApp('/training', trainingServer(startState()));
    await screenLoaded();

    await chooseRun('rotate-v2');
    await userEvent.click(within(inspector()).getByRole('button', { name: 'New run' }));

    expect(primary().textContent).toBe('Start training');
    expect(field('Name')).toBeTruthy();
  });

  it('waits while a job runs, and says so', async () => {
    const server = trainingServer({ ...startState(), job: RUNNING });
    renderApp('/training', server);
    await screenLoaded();
    await chooseRun('rotate-v2');

    await vi.waitFor(() => expect(primary().textContent).toBe('Job running'));
    expect(primary().disabled).toBe(true);
    await userEvent.keyboard('{Meta>}{Enter}{/Meta}');
    expect(postedBody(server, '/api/training/resume')).toBeUndefined();
  });
});

describe('the runs', () => {
  it('lists each run newest first with its steps, data seen and chart', async () => {
    renderApp('/training', trainingServer(startState()));
    await screenLoaded();

    const list = screen.getByRole('list', { name: 'Training runs' });
    const cards = Array.from(list.children) as HTMLElement[];

    expect(cards.map((card) => card.querySelector('.training-run__name')!.textContent)).toEqual([
      'pixie-draw-v1',
      'rotate-v2',
    ]);
    expect(cards[0]!.textContent).toContain('42% of the data seen');
    expect(cards[1]!.textContent).toContain('Step 2,000 of 2,000');
    expect(cards[1]!.textContent).toContain('27 s a step');
    expect(within(cards[1]!).getByRole('img').getAttribute('aria-label')).toBe(
      'Loss of rotate-v2 over 2,000 steps, val loss 0.0805 at step 2,000.',
    );
  });

  it('marks the run being trained', async () => {
    const state = startState();
    state.runs = [{ ...state.runs[0]!, isTraining: true }, state.runs[1]!];
    renderApp('/training', trainingServer(state));
    await screenLoaded();

    expect(screen.getAllByText('Training now')).toHaveLength(1);
  });

  it('says a run that has just started has no steps yet', async () => {
    const state = startState();
    state.runs = [{ ...state.runs[0]!, step: 0, loss: [], val: [], isTraining: true }];
    renderApp('/training', trainingServer(state));

    expect(await screen.findByText(/^No steps yet/)).toBeTruthy();
  });

  it('says what to do when there is no run yet', async () => {
    renderApp('/training', trainingServer({ ...startState(), runs: [] }));

    expect(await screen.findByText('No training runs yet')).toBeTruthy();
  });
});
