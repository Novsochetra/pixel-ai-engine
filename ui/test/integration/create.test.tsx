import { cleanup, screen, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { createServer, postedBody, startState } from './create-server';
import { RUNNING, renderApp } from './render-app';

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
});

const inspector = () => screen.getByRole('complementary', { name: 'Inspector' });

const generateButton = () => screen.getByRole('button', { name: /^(Generate|Job running)/ });

const openSheet = () =>
  screen.getAllByRole('dialog', { hidden: true }).find((dialog) => dialog.hasAttribute('open'))!;

async function fillPrompt(text: string) {
  const field = await within(inspector()).findByLabelText(/What to draw/);

  await userEvent.type(field, text);
}

describe('the create screen', () => {
  it('shows what was made, newest first, with its settings', async () => {
    renderApp('/create', createServer(startState()));

    const list = await screen.findByRole('list', { name: 'Made so far' });
    const cards = [...list.querySelectorAll<HTMLElement>('.made-card')];

    expect(cards.map((card) => card.querySelector('.made-card__title')!.textContent)).toEqual([
      'a lava dragon',
      'a frog wizard',
    ]);
    expect(within(cards[0]!).getByText(/128 px · rotate-v2 · final/)).toBeTruthy();
    expect(within(cards[0]!).getAllByRole('img')).toHaveLength(2);
  });

  it('opens a made character large, with zoom and its details', async () => {
    renderApp('/create', createServer(startState()));

    await userEvent.click(await screen.findByRole('button', { name: /^a lava dragon/ }));
    const sheet = openSheet();

    expect(within(sheet).getByRole('img', { name: 'a lava dragon, Character 1' })).toBeTruthy();
    await userEvent.click(within(sheet).getByRole('button', { name: 'Zoom in' }));
    expect(within(sheet).getByRole('status').textContent).toBe('2×');
    expect(within(sheet).getByText('create-v1 · final')).toBeTruthy();
  });

  it('says what to do when nothing was made yet', async () => {
    renderApp('/create', createServer({ ...startState(), items: [] }));

    expect(await screen.findByText('Nothing made yet')).toBeTruthy();
    expect(screen.getByText('Write what to draw, then Generate.')).toBeTruthy();
  });

  it('posts the filled form when Generate is pressed', async () => {
    const server = createServer(startState());
    renderApp('/create', server);

    await fillPrompt('a frog wizard');
    await userEvent.type(within(inspector()).getByLabelText('Pose'), 'sitting');
    await userEvent.click(
      within(inspector()).getByRole('button', { name: 'Characters: one more' }),
    );
    await userEvent.selectOptions(within(inspector()).getByLabelText('Sprite size'), '64');
    await userEvent.click(generateButton());

    await vi.waitFor(() => expect(postedBody(server)).toBeDefined());
    expect(postedBody(server)).toEqual({
      prompt: 'a frog wizard',
      pose: 'sitting',
      facing: 'front',
      characters: 3,
      sprite: '64',
      drawWith: '',
      drawingModel: 'flux2-klein-4b',
      turnWith: 'runs/rotate-v1/final',
      turningModel: 'flux2-klein-4b',
    });
  });

  it('generates with ⌘↩ from the form', async () => {
    const server = createServer(startState());
    renderApp('/create', server);

    await fillPrompt('a red slime');
    await userEvent.keyboard('{Meta>}{Enter}{/Meta}');

    await vi.waitFor(() => expect(postedBody(server)?.prompt).toBe('a red slime'));
  });

  it('shows a refused form in words, until it is closed', async () => {
    const detail = 'Characters must be a whole number from 1 to 8.';
    renderApp('/create', createServer({ ...startState(), refusal: { status: 400, detail } }));

    await fillPrompt('a frog');
    await userEvent.click(generateButton());

    const alert = await within(inspector()).findByRole('alert');
    expect(alert.textContent).toContain(detail);

    await userEvent.click(within(alert).getByRole('button', { name: 'Close the error' }));
    expect(within(inspector()).queryByRole('alert')).toBeNull();
  });

  it('waits while a job runs, and says so', async () => {
    const server = createServer({ ...startState(), job: RUNNING });
    renderApp('/create', server);

    await fillPrompt('a frog');

    await vi.waitFor(() => expect(generateButton().textContent).toBe('Job running'));
    expect((generateButton() as HTMLButtonElement).disabled).toBe(true);
    await userEvent.keyboard('{Meta>}{Enter}{/Meta}');
    expect(postedBody(server)).toBeUndefined();
  });

  it('turns off a create LoRA for a pose it never learned, and says why', async () => {
    const server = createServer(startState());
    renderApp('/create', server);

    await fillPrompt('a dragon');
    const drawWith = within(inspector()).getByLabelText('Draw with') as HTMLSelectElement;
    await userEvent.selectOptions(drawWith, 'runs/create-v1/final');
    await userEvent.type(within(inspector()).getByLabelText('Pose'), 'flying');

    expect(drawWith.disabled).toBe(true);
    expect(within(inspector()).getByText(/draws only standing sprites/)).toBeTruthy();

    await userEvent.click(generateButton());
    await vi.waitFor(() => expect(postedBody(server)?.drawWith).toBe(''));
  });

  it('turns nothing for a side view', async () => {
    renderApp('/create', createServer(startState()));

    await fillPrompt('a dragon');
    await userEvent.click(within(inspector()).getByRole('button', { name: 'Side' }));

    const turnWith = within(inspector()).getByLabelText('Turn with') as HTMLSelectElement;
    expect(turnWith.disabled).toBe(true);
    expect(turnWith.value).toBe('');
    expect(within(inspector()).getByText(/flipped for the left, not turned/)).toBeTruthy();
  });

  it('refreshes the gallery when the job ends', async () => {
    const state = { ...startState(), job: RUNNING };
    state.items = [];
    const server = createServer(state);
    renderApp('/create', server);

    expect(await screen.findByText('Nothing made yet')).toBeTruthy();
    state.job = { ...RUNNING, job: { ...RUNNING.job!, status: 'done' } };
    state.items = startState().items;

    expect(
      await screen.findByRole('list', { name: 'Made so far' }, { timeout: 4000 }),
    ).toBeTruthy();
  });
});
