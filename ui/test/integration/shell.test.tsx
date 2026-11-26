import { cleanup, screen, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { NO_JOB, fakeServer, renderApp } from './render-app';

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
  window.localStorage.clear();
});

const sidebar = () => screen.getAllByRole('navigation', { name: 'Sections' })[0]!;

describe('the layout shell', () => {
  it('opens on Create and lists every section in the sidebar', async () => {
    renderApp('/', fakeServer(NO_JOB));

    expect(await screen.findByRole('heading', { level: 1, name: 'Create' })).toBeTruthy();
    const rows = within(sidebar()).getAllByRole('link');
    expect(rows.map((row) => row.textContent)).toEqual([
      'Create',
      'Rotate',
      'Animate',
      'Landscape',
      'Library',
      'Training',
    ]);
  });

  it('moves to a section from the sidebar and marks it current', async () => {
    renderApp('/create', fakeServer(NO_JOB));

    await userEvent.click(within(sidebar()).getByRole('link', { name: 'Library' }));

    expect(screen.getByRole('heading', { level: 1, name: 'Library' })).toBeTruthy();
    expect(
      within(sidebar()).getByRole('link', { name: 'Library' }).getAttribute('aria-current'),
    ).toBe('page');
  });

  it('hides and shows the inspector', async () => {
    const { container } = renderApp('/create', fakeServer(NO_JOB));
    const button = await screen.findByRole('button', { name: 'Inspector' });
    const frame = container.querySelector('.screen')!;

    expect(frame.getAttribute('data-inspector')).toBe('shown');
    await userEvent.click(button);

    expect(frame.getAttribute('data-inspector')).toBe('hidden');
    expect(button.getAttribute('aria-pressed')).toBe('false');
  });

  it('switches the appearance and remembers it', async () => {
    document.documentElement.dataset.appearance = 'dark';
    renderApp('/create', fakeServer(NO_JOB));

    await userEvent.click(screen.getAllByRole('button', { name: 'Use light appearance' })[0]!);

    expect(document.documentElement.dataset.appearance).toBe('light');
    expect(window.localStorage.getItem('pixel.appearance')).toContain('"choice":"light"');
  });
});
