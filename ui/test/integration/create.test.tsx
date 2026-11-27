import { cleanup, screen, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { createServer, HERO, postedBody, startState } from './create-server';
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
  it('shows what was made as a grid, newest first, its first character standing for it', async () => {
    renderApp('/create', createServer(startState()));

    const list = await screen.findByRole('list', { name: 'Made so far' });
    const tiles = [...list.querySelectorAll<HTMLElement>('.made-tile')];

    expect(tiles.map((tile) => tile.querySelector('.made-tile__title')!.textContent)).toEqual([
      'a lava dragon',
      'a frog wizard',
    ]);
    expect(within(tiles[0]!).getByText('Nov 24 · 2 characters')).toBeTruthy();
    expect(within(tiles[0]!).getByRole('img').getAttribute('alt')).toBe(
      'a lava dragon, Character 1',
    );
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
    await userEvent.selectOptions(within(inspector()).getByLabelText('Palette'), 'pico-8');
    await userEvent.selectOptions(within(inspector()).getByLabelText('Max colours'), '8');
    await userEvent.click(generateButton());

    await vi.waitFor(() => expect(postedBody(server)).toBeDefined());
    expect(postedBody(server)).toEqual({
      prompt: 'a frog wizard',
      pose: 'sitting',
      facing: 'front',
      characters: 3,
      sprite: '64',
      palette: 'pico-8',
      colours: 8,
      drawWith: '',
      drawingModel: 'flux2-klein-base-4b',
      reference: '',
    });
  });

  it('starts with the newest create LoRA on the base model, and draws fast with none', async () => {
    renderApp('/create', createServer(startState()));
    const drawWith = await within(inspector()).findByLabelText('Draw with');
    const drawingModel = () => within(inspector()).getByLabelText('Drawing model');

    expect(drawWith).toHaveProperty('value', 'runs/create-v1/final');
    expect(drawingModel()).toHaveProperty('value', 'flux2-klein-base-4b');
    await userEvent.selectOptions(drawWith, '');
    expect(drawingModel()).toHaveProperty('value', 'flux2-klein-4b');
    await userEvent.selectOptions(drawWith, 'runs/create-v1/final');
    expect(drawingModel()).toHaveProperty('value', 'flux2-klein-base-4b');
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

  it('draws a side view only with a create LoRA that learnt sides', async () => {
    const server = createServer(startState());
    renderApp('/create', server);

    await fillPrompt('a knight');
    await userEvent.click(within(inspector()).getByRole('button', { name: 'Side' }));
    const drawWith = within(inspector()).getByLabelText('Draw with') as HTMLSelectElement;

    expect([...drawWith.options].map((option) => option.value)).toEqual([
      '',
      'runs/pixie-draw-v1/final',
    ]);
    expect(drawWith.value).toBe('');
    await userEvent.selectOptions(drawWith, 'runs/pixie-draw-v1/final');
    await userEvent.click(generateButton());
    await vi.waitFor(() =>
      expect(postedBody(server)).toMatchObject({
        facing: 'side',
        drawWith: 'runs/pixie-draw-v1/final',
      }),
    );
  });

  it('only draws, leaving the turning to Rotate', async () => {
    renderApp('/create', createServer(startState()));

    await fillPrompt('a dragon');

    expect(within(inspector()).queryByText('Turning')).toBeNull();
    expect(within(inspector()).queryByLabelText('Turn with')).toBeNull();
    expect(within(inspector()).getByText(/Turn it on Rotate/)).toBeTruthy();
    await userEvent.click(within(inspector()).getByRole('button', { name: 'Side' }));
    expect(within(inspector()).getByText(/The left is its mirror/)).toBeTruthy();
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

  it('uploads a reference, shows it, and sends it with Generate', async () => {
    const server = createServer(startState());
    renderApp('/create', server);

    await fillPrompt('a hero');
    const png = new File(['png'], 'hero.png', { type: 'image/png' });
    await userEvent.upload(within(inspector()).getByLabelText('PNG to upload'), png);

    await vi.waitFor(() =>
      expect(within(inspector()).getByLabelText('Reference')).toHaveProperty('value', HERO.value),
    );
    expect(within(inspector()).getByRole('img', { name: `Reference: ${HERO.label}` })).toBeTruthy();
    await userEvent.click(generateButton());

    await vi.waitFor(() => expect(postedBody(server)?.reference).toBe(HERO.value));
  });

  it('picks an earlier upload as the reference, or none', async () => {
    const server = createServer({ ...startState(), uploads: [HERO] });
    renderApp('/create', server);

    await fillPrompt('a hero');
    const picker = await within(inspector()).findByRole('option', { name: HERO.label });
    await userEvent.selectOptions(within(inspector()).getByLabelText('Reference'), picker);
    await userEvent.selectOptions(within(inspector()).getByLabelText('Reference'), 'None');
    await userEvent.click(generateButton());

    await vi.waitFor(() => expect(postedBody(server)?.reference).toBe(''));
  });
});
