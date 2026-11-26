import { cleanup, screen, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { CHARACTERS, KNIGHT, NOT_ANALYZED, libraryServer } from './library-server';
import { renderApp } from './render-app';

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
});

const SERVER = {
  '/api/characters': CHARACTERS,
  '/api/characters/pac/train/0': KNIGHT,
  '/api/flagged': NOT_ANALYZED,
  '/api/exports': { exports: [] },
};

const openSheet = () =>
  screen.getAllByRole('dialog', { hidden: true }).find((dialog) => dialog.hasAttribute('open'))!;

const knightTile = () => screen.findByRole('button', { name: /pac\/train\/0/ });

describe('the library', () => {
  it('shows the dataset as a grid of sharp pixel art', async () => {
    renderApp('/library', libraryServer(SERVER));

    const tile = await knightTile();
    const art = within(tile).getByRole('img', { name: 'pac/train/0, front' });

    expect(art.getAttribute('src')).toBe('/api/thumbs/x.png');
    expect(art.parentElement!.classList.contains('pixel-art')).toBe(true);
    expect(within(tile).getByText('a knight with a spear')).toBeTruthy();
  });

  it('shows the records of the selected character in the inspector', async () => {
    renderApp('/library', libraryServer(SERVER));

    await userEvent.click(await knightTile());

    const inspector = screen.getByRole('complementary', { name: 'Inspector' });
    expect(await within(inspector).findByText('CC-BY-NC-4.0')).toBeTruthy();
    expect(within(inspector).getByText('duplicate')).toBeTruthy();
    expect(within(inspector).getByText('Exact copy of pac/test/0, so it is dropped.')).toBeTruthy();
  });

  it('opens a picture large, with zoom, its views and a download', async () => {
    renderApp('/library', libraryServer(SERVER));

    await userEvent.click(await knightTile());
    await userEvent.click(screen.getByRole('button', { name: 'Open' }));
    const sheet = openSheet();

    expect(within(sheet).getByRole('img', { name: 'pac/train/0, front' })).toBeTruthy();
    await userEvent.click(within(sheet).getByRole('button', { name: 'Zoom in' }));
    expect(within(sheet).getByRole('status').textContent).toBe('2×');

    await userEvent.click(within(sheet).getByRole('button', { name: 'left' }));
    expect(within(sheet).getByRole('status').textContent).toBe('1×');
    expect(within(sheet).getByRole('link', { name: 'Download' }).getAttribute('href')).toBe(
      '/api/images/pac/train/0/left.png',
    );
  });

  it('sends a search to the server once typing pauses', async () => {
    const server = libraryServer(SERVER);
    renderApp('/library', server);

    await userEvent.type(await screen.findByRole('searchbox'), 'frog');

    await vi.waitFor(() => expect(server).toHaveBeenCalledWith('/api/characters?page=1&q=frog'));
    expect(server).not.toHaveBeenCalledWith('/api/characters?page=1&q=fro');
  });

  it('says what to run when nothing is analyzed or exported yet', async () => {
    renderApp('/library', libraryServer(SERVER));

    await userEvent.click(await screen.findByRole('button', { name: 'Flagged' }));
    expect(await screen.findByText('uv run pixel analyze')).toBeTruthy();

    await userEvent.click(screen.getByRole('button', { name: 'Exports' }));
    expect(await screen.findByText('No exports yet')).toBeTruthy();
  });

  it('offers Try again when the server fails, and loads once it answers', async () => {
    const answers: Record<string, object | number> = { ...SERVER, '/api/characters': 500 };
    renderApp('/library', libraryServer(answers));

    const retry = await screen.findByRole('button', { name: 'Try again' });
    expect(screen.getByText(/The server answered 500/)).toBeTruthy();

    answers['/api/characters'] = CHARACTERS;
    await userEvent.click(retry);

    expect(await knightTile()).toBeTruthy();
  });
});
