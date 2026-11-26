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

describe('the animate gallery and player', () => {
  it('lists the runs newest first, and plays the newest clip', async () => {
    renderApp('/animate', animateServer(startState()));

    const list = await screen.findByRole('list', { name: 'Animated so far' });
    const titles = within(list)
      .getAllByRole('heading')
      .map((heading) => heading.textContent);

    expect(titles).toEqual(['dragon', 'slime.png']);
    expect((await playerShown()).getByRole('img', { name: 'dragon, Front · idle' })).toBeTruthy();
    expect(
      screen.getByRole('button', { name: 'dragon, Front · idle' }).getAttribute('aria-pressed'),
    ).toBe('true');
  });

  it('steps the frames, and stays on one when paused', async () => {
    const view = await renderAndWait();

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
    const view = await renderAndWait();

    expect(view.getByRole('button', { name: 'Play' })).toBeTruthy();
    await userEvent.click(view.getByRole('button', { name: 'Previous frame' }));
    expect(frameText()).toBe('Frame 8 of 8');
  });

  it('switches the clip by view and by action', async () => {
    const view = await renderAndWait();

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

  it('plays a clip chosen in the gallery', async () => {
    renderApp('/animate', animateServer(startState()));

    await userEvent.click(await screen.findByRole('button', { name: 'slime.png, hops' }));

    expect((await playerShown()).getByRole('img', { name: 'slime.png, hops' })).toBeTruthy();
  });

  it('says what to do when nothing was animated yet', async () => {
    renderApp('/animate', animateServer({ ...startState(), runs: [] }));

    expect(await screen.findByText('Nothing animated yet')).toBeTruthy();
    expect(screen.queryByRole('region', { name: 'Player' })).toBeNull();
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

async function renderAndWait() {
  renderApp('/animate', animateServer(startState()));

  return playerShown();
}
