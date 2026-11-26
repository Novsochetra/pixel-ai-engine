import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { render } from '@testing-library/react';
import { MemoryRouter } from 'react-router';
import { vi } from 'vitest';
import { App } from '@/App';
import type { JobView } from '@/jobs/jobs-client';

export const NO_JOB: JobView = { job: null, progress: null, step: '', log: '' };

export const RUNNING: JobView = {
  job: {
    id: '20261124-153908',
    kind: 'generate',
    title: 'Make a lava dragon',
    status: 'running',
    stopping: false,
    startedAt: new Date().toISOString(),
    endedAt: null,
  },
  progress: 0.42,
  step: 'turning 2 of 3: s0 back...',
  log: 'Loading pipeline components...\nturning 2 of 3: s0 back...',
};

// The server is replaced by a fetch that answers the job paths with this view, and no other.
export function fakeServer(current: JobView) {
  return vi.fn(async (url: string, init?: RequestInit) => {
    if (!url.startsWith('/api/jobs/')) {
      return new Response('{}', { status: 404 });
    }

    const isStop = url === '/api/jobs/stop' && init?.method === 'POST';
    const view =
      isStop && current.job ? { ...current, job: { ...current.job, status: 'stopped' } } : current;

    return new Response(JSON.stringify(view), { headers: { 'Content-Type': 'application/json' } });
  });
}

export function renderApp(path: string, server: ReturnType<typeof fakeServer>) {
  vi.stubGlobal('fetch', server);
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });

  return render(
    <QueryClientProvider client={client}>
      <MemoryRouter initialEntries={[path]}>
        <App />
      </MemoryRouter>
    </QueryClientProvider>,
  );
}
