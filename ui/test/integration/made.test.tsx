import { cleanup, screen, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { DRAGON, createServer, startState } from './create-server';
import { DRAGON_RUN, animateServer, startState as animateStart } from './animate-server';
import { rotateServer, startState as rotateStart } from './rotate-server';
import { renderApp } from './render-app';

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
});

const openSheet = () =>
  screen.getAllByRole('dialog', { hidden: true }).find((dialog) => dialog.hasAttribute('open'))!;

const titles = () =>
  [...screen.getByRole('list', { name: 'Made so far' }).querySelectorAll('.made-tile')].map(
    (tile) => tile.querySelector('.made-tile__title')!.textContent,
  );

function posts(server: { mock: { calls: [string, RequestInit?][] } }, path: string) {
  return server.mock.calls
    .filter(([url, init]) => url === path && init?.method === 'POST')
    .map(([, init]) => JSON.parse(String(init!.body)));
}

async function openDragon() {
  const list = await screen.findByRole('list', { name: 'Made so far' });

  await userEvent.click(list.querySelector<HTMLElement>('.made-tile__open')!);
}

describe('deleting what was made', () => {
  it('asks first, and keeps it when Keep is pressed', async () => {
    const server = createServer(startState());
    renderApp('/create', server);

    await openDragon();
    await userEvent.click(within(openSheet()).getByRole('button', { name: 'Delete' }));

    expect(within(openSheet()).getByText(/the 2 characters made with it/)).toBeTruthy();
    await userEvent.click(within(openSheet()).getByRole('button', { name: 'Keep' }));

    expect(posts(server, '/api/generated/trash')).toEqual([]);
  });

  it('moves it to the trash, takes it off the gallery, and Undo brings it back', async () => {
    const server = createServer(startState());
    renderApp('/create', server);

    await openDragon();
    await userEvent.click(within(openSheet()).getByRole('button', { name: 'Delete' }));
    await userEvent.click(within(openSheet()).getByRole('button', { name: 'Delete' }));

    expect(posts(server, '/api/generated/trash')).toEqual([{ folder: DRAGON.folder }]);
    const message = await screen.findByText('Deleted “a lava dragon”.');
    const toast = message.closest<HTMLElement>('[role="status"]')!;
    await vi.waitFor(() => expect(titles()).toEqual(['a frog wizard']));

    await userEvent.click(within(toast).getByRole('button', { name: 'Undo' }));

    expect(posts(server, '/api/generated/restore')).toEqual([
      { folder: DRAGON.folder, trashed: DRAGON.folder },
    ]);
    await vi.waitFor(() => expect(titles()).toEqual(['a lava dragon', 'a frog wizard']));
    expect(screen.queryByText('Deleted “a lava dragon”.')).toBeNull();
  });
});

const askSheet = () =>
  screen
    .getAllByRole('dialog', { hidden: true })
    .find((dialog) => dialog.hasAttribute('open') && within(dialog).queryByText('Delete?'))!;

describe('the trash button in the corner of a card', () => {
  it('asks in a small sheet, then deletes without opening the card', async () => {
    const server = createServer(startState());
    renderApp('/create', server);

    await userEvent.click(await screen.findByRole('button', { name: 'Delete a lava dragon' }));
    expect(within(askSheet()).getByText(/the 2 characters made with it/)).toBeTruthy();
    await userEvent.click(within(askSheet()).getByRole('button', { name: 'Delete' }));

    expect(posts(server, '/api/generated/trash')).toEqual([{ folder: DRAGON.folder }]);
    await vi.waitFor(() => expect(titles()).toEqual(['a frog wizard']));
    expect(await screen.findByText('Deleted “a lava dragon”.')).toBeTruthy();
  });

  it('keeps the card when Keep is pressed', async () => {
    const server = createServer(startState());
    renderApp('/create', server);

    await userEvent.click(await screen.findByRole('button', { name: 'Delete a frog wizard' }));
    await userEvent.click(within(askSheet()).getByRole('button', { name: 'Keep' }));

    expect(posts(server, '/api/generated/trash')).toEqual([]);
    expect(titles()).toEqual(['a lava dragon', 'a frog wizard']);
  });

  it('deletes a whole animation from Animate', async () => {
    const server = animateServer(animateStart());
    renderApp('/animate', server);

    await userEvent.click(await screen.findByRole('button', { name: 'Delete dragon' }));
    expect(within(askSheet()).getByText(/the animation of “dragon” and its 4 clips/)).toBeTruthy();
    await userEvent.click(within(askSheet()).getByRole('button', { name: 'Delete' }));

    expect(posts(server, '/api/animated/trash')).toEqual([{ folder: DRAGON_RUN.folder }]);
    await vi.waitFor(() =>
      expect(screen.queryByRole('button', { name: 'Delete dragon' })).toBeNull(),
    );
  });

  it('deletes an animation from its player sheet, closing the sheet', async () => {
    const server = animateServer(animateStart());
    renderApp('/animate', server);

    await userEvent.click(await screen.findByRole('button', { name: /^dragon/ }));
    await userEvent.click(within(openSheet()).getByRole('button', { name: 'Delete' }));
    await userEvent.click(within(openSheet()).getByRole('button', { name: 'Delete' }));

    expect(posts(server, '/api/animated/trash')).toEqual([{ folder: DRAGON_RUN.folder }]);
    await vi.waitFor(() => expect(screen.queryByRole('region', { name: 'Player' })).toBeNull());
  });

  it('deletes a turned character from Rotate, with its whole set', async () => {
    const server = rotateServer(rotateStart());
    renderApp('/rotate', server);

    await userEvent.click(await screen.findByRole('button', { name: 'Delete a knight' }));
    expect(within(askSheet()).getByText(/in Create and Rotate/)).toBeTruthy();
    await userEvent.click(within(askSheet()).getByRole('button', { name: 'Delete' }));

    expect(posts(server, '/api/generated/trash')).toEqual([{ folder: 'knight' }]);
  });
});
