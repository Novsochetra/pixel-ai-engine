import { cleanup, fireEvent, screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { renderApp } from './render-app';
import { postedBody, startState, trainingServer } from './training-server';

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
});

const layers = () => [...document.querySelectorAll<HTMLElement>('.screen-layer')];

async function openRun(name: string) {
  const cards = await screen.findByRole('list', { name: 'Training runs' });

  await userEvent.click(within(cards).getByRole('link', { name: new RegExp(`^${name}`) }));
  await screen.findByRole('heading', { name, level: 1 });
}

describe('the screen stack', () => {
  it('keeps Training under a run, unseen and inert, and brings the same screen back', async () => {
    const server = trainingServer(startState());
    renderApp('/training', server);
    await openRun('rotate-v2');
    const runs = screen.queryByRole('list', { name: 'Training runs' });
    const under = layers()[0]!;

    expect(runs).toBeNull();
    expect(under.inert).toBe(true);
    expect(under.getAttribute('aria-hidden')).toBe('true');

    await userEvent.click(screen.getByRole('link', { name: 'Back to Training' }));

    await waitFor(() => expect(layers()).toEqual([under]));
    expect(under.inert).toBe(false);
    expect(screen.getByRole('heading', { name: 'Training', level: 1 })).toBeTruthy();
  });

  it('runs ⌘↩ on the screen shown only, not on the one under it', async () => {
    const server = trainingServer(startState());
    renderApp('/training', server);
    await userEvent.type(await screen.findByLabelText('Name'), 'rotate-v3');
    await openRun('rotate-v2');

    fireEvent.keyDown(window, { key: 'Enter', metaKey: true });

    await waitFor(() => expect(postedBody(server, '/api/training/resume')).toBeTruthy());
    expect(postedBody(server, '/api/training/start')).toBeUndefined();
  });

  it('swaps sections, leaving only the section arrived at', async () => {
    const server = trainingServer(startState());
    renderApp('/training', server);
    await openRun('rotate-v2');

    await userEvent.click(screen.getAllByRole('link', { name: 'Library' })[0]!);

    await screen.findByRole('heading', { name: 'Library', level: 1 });
    await waitFor(() => expect(layers()).toHaveLength(1));
  });
});
