import { cleanup, screen, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { animateServer, DRAGON_RUN, startState } from './animate-server';
import { RUNNING, renderApp } from './render-app';

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
});

const player = () => screen.getByRole('region', { name: 'Player' });

const frameText = () => within(player()).getByText(/^Frame \d+ of \d+$/).textContent;

const openSheet = () =>
  screen.getAllByRole('dialog', { hidden: true }).find((dialog) => dialog.hasAttribute('open'));

async function playerShown() {
  return within(await screen.findByRole('region', { name: 'Player' }));
}

function reduceMotion() {
  const matchMedia = (query: string) => ({
    matches: query.includes('reduced-motion'),
    addEventListener: () => {},
    removeEventListener: () => {},
  });

  vi.stubGlobal('matchMedia', matchMedia);
}

async function openRun(name: RegExp) {
  await userEvent.click(await screen.findByRole('button', { name }));

  return playerShown();
}

describe('the animate gallery and player', () => {
  it('lists the runs as a grid, newest first, with nothing playing yet', async () => {
    renderApp('/animate', animateServer(startState()));

    const list = await screen.findByRole('list', { name: 'Animated so far' });
    const titles = [...list.querySelectorAll('.made-tile__title')].map(
      (title) => title.textContent,
    );

    expect(titles).toEqual(['dragon', 'slime.png']);
    expect(within(list).getByText('Nov 24 · 4 clips')).toBeTruthy();
    expect(within(list).getByRole('img', { name: 'dragon, Front · idle' })).toBeTruthy();
    expect(screen.queryByRole('region', { name: 'Player' })).toBeNull();
  });

  it('plays a run in a sheet, from its first clip', async () => {
    renderApp('/animate', animateServer(startState()));

    const view = await openRun(/^slime\.png/);

    expect(within(openSheet()!).getByRole('heading', { name: 'slime.png' })).toBeTruthy();
    expect(view.getByRole('img', { name: 'slime.png, hops' })).toBeTruthy();
  });

  it('closes the sheet, and the player with it', async () => {
    renderApp('/animate', animateServer(startState()));

    await openRun(/^dragon/);
    await userEvent.click(within(openSheet()!).getByRole('button', { name: 'Close' }));

    await vi.waitFor(() => expect(screen.queryByRole('region', { name: 'Player' })).toBeNull());
  });

  it('steps the frames, and stays on one when paused', async () => {
    const view = await renderAndOpen();

    await vi.waitFor(() => expect(frameText()).not.toBe('Frame 1 of 8'), { timeout: 2000 });
    await userEvent.click(view.getByRole('button', { name: 'Pause' }));
    const paused = frameText();
    await new Promise((resolve) => setTimeout(resolve, 600));

    expect(frameText()).toBe(paused);
    await userEvent.click(view.getByRole('button', { name: 'Next frame' }));
    expect(frameText()).not.toBe(paused);
  });

  it('waits for Play when motion is reduced', async () => {
    reduceMotion();
    const view = await renderAndOpen();

    expect(view.getByRole('button', { name: 'Play' })).toBeTruthy();
    await userEvent.click(view.getByRole('button', { name: 'Previous frame' }));
    expect(frameText()).toBe('Frame 8 of 8');
  });

  it('switches the clip by view and by action', async () => {
    const view = await renderAndOpen();

    await userEvent.click(view.getByRole('button', { name: 'Left' }));
    await userEvent.selectOptions(view.getByLabelText('Action'), 'flying');

    expect(view.getByRole('img', { name: 'dragon, Left · flying' })).toBeTruthy();
    expect(view.getByRole('link', { name: 'Download sheet' }).getAttribute('href')).toBe(
      DRAGON_RUN.clips[3]!.sheet,
    );
    expect(view.getByRole('link', { name: 'Raw video' }).getAttribute('href')).toBe(
      DRAGON_RUN.clips[3]!.raw,
    );
  });

  it('says what to do when nothing was animated yet', async () => {
    renderApp('/animate', animateServer({ ...startState(), runs: [] }));

    expect(await screen.findByText('Nothing animated yet')).toBeTruthy();
  });

  it('refreshes the gallery when the job ends', async () => {
    const state = { ...startState(), job: RUNNING };
    state.runs = [];
    renderApp('/animate', animateServer(state));

    expect(await screen.findByText('Nothing animated yet')).toBeTruthy();
    state.job = { ...RUNNING, job: { ...RUNNING.job!, status: 'done' } };
    state.runs = startState().runs;

    expect(
      await screen.findByRole('list', { name: 'Animated so far' }, { timeout: 4000 }),
    ).toBeTruthy();
  });
});

async function renderAndOpen() {
  renderApp('/animate', animateServer(startState()));

  return openRun(/^dragon/);
}
