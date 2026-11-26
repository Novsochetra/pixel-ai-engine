import { cleanup, screen, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { NO_JOB, RUNNING, fakeServer, renderApp } from './render-app';

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
});

const sidebarJob = async () =>
  (await screen.findAllByRole('button', { name: /Make a lava dragon/ }))[0]!;

describe('the job status', () => {
  it('shows nothing when no job ran yet', async () => {
    const server = fakeServer(NO_JOB);
    renderApp('/create', server);

    await vi.waitFor(() =>
      expect(server).toHaveBeenCalledWith('/api/jobs/current', expect.anything()),
    );

    expect(screen.queryByRole('progressbar', { name: 'Job progress' })).toBeNull();
  });

  it('shows a running job with its progress', async () => {
    renderApp('/create', fakeServer(RUNNING));

    const card = await sidebarJob();

    expect(within(card).getByText('42%')).toBeTruthy();
    expect(within(card).getByRole('progressbar').getAttribute('aria-valuenow')).toBe('42');
  });

  it('opens the log and stops the job only after asking', async () => {
    const server = fakeServer(RUNNING);
    renderApp('/create', server);

    await userEvent.click(await sidebarJob());
    const sheet = screen
      .getAllByRole('dialog', { hidden: true })
      .find((dialog) => dialog.hasAttribute('open'))!;

    expect(within(sheet).getByLabelText('Job log').textContent).toContain('turning 2 of 3');
    await userEvent.click(within(sheet).getByRole('button', { name: 'Stop job' }));
    expect(server).not.toHaveBeenCalledWith('/api/jobs/stop', expect.anything());

    await userEvent.click(within(sheet).getByRole('button', { name: 'Stop' }));

    await vi.waitFor(() =>
      expect(server).toHaveBeenCalledWith(
        '/api/jobs/stop',
        expect.objectContaining({ method: 'POST' }),
      ),
    );
  });
});
