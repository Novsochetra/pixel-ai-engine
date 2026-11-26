import { cleanup, screen, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { renderApp } from '../integration/render-app';
import { startState, trainingServer } from '../integration/training-server';

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
});

// The Training screen once cut or morphed a picture of itself into a run's screen and back, losing
// what was typed; now it stays live under the run and comes back as it was left.
describe('moving between Training and a run', () => {
  it('brings Training back with what was typed in it', async () => {
    renderApp('/training', trainingServer(startState()));
    await userEvent.type(await screen.findByLabelText('Name'), 'rotate-v3');
    const cards = await screen.findByRole('list', { name: 'Training runs' });

    await userEvent.click(within(cards).getByRole('link', { name: /^rotate-v2/ }));
    await userEvent.click(await screen.findByRole('link', { name: 'Back to Training' }));

    expect((await screen.findByLabelText('Name')) as HTMLInputElement).toHaveProperty(
      'value',
      'rotate-v3',
    );
  });
});
