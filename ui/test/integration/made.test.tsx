import { cleanup, screen, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { DRAGON, createServer, startState } from './create-server';
import { renderApp } from './render-app';

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
});

const openSheet = () =>
  screen.getAllByRole('dialog', { hidden: true }).find((dialog) => dialog.hasAttribute('open'))!;

const titles = () =>
  within(screen.getByRole('list', { name: 'Made so far' }))
    .getAllByRole('button')
    .map((card) => card.querySelector('.made-card__title')!.textContent);

function posts(server: ReturnType<typeof createServer>, path: string) {
  return server.mock.calls
    .filter(([url, init]) => url === path && init?.method === 'POST')
    .map(([, init]) => JSON.parse(String(init!.body)));
}

async function openDragon() {
  const list = await screen.findByRole('list', { name: 'Made so far' });

  await userEvent.click(within(list).getAllByRole('button')[0]!);
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
