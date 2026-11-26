import { describe, expect, it } from 'vitest';
import { elapsedText, percentText, statusLabel } from '@/jobs/job-text';
import type { Job } from '@/jobs/jobs-client';

const JOB: Job = {
  id: '20261124-153908',
  kind: 'animate',
  title: 'Animate a dragon',
  status: 'running',
  stopping: false,
  startedAt: '2026-11-24T08:00:00+00:00',
  endedAt: null,
};

describe('statusLabel', () => {
  it('names each status', () => {
    expect(statusLabel(JOB)).toBe('Running');
    expect(statusLabel({ ...JOB, status: 'failed' })).toBe('Failed');
  });

  it('says a job is stopping before it has stopped', () => {
    expect(statusLabel({ ...JOB, stopping: true })).toBe('Stopping…');
  });
});

describe('percentText', () => {
  it('rounds to a whole percent', () => {
    expect(percentText(0.426)).toBe('43%');
  });

  it('says nothing when the share done is unknown', () => {
    expect(percentText(null)).toBe('');
  });
});

describe('elapsedText', () => {
  const now = new Date('2026-11-24T09:05:00+00:00');

  it('counts seconds, minutes and hours', () => {
    expect(elapsedText('2026-11-24T09:04:20+00:00', null, now)).toBe('40 s');
    expect(elapsedText('2026-11-24T08:55:00+00:00', null, now)).toBe('10 min');
    expect(elapsedText(JOB.startedAt, null, now)).toBe('1 h 5 min');
    expect(elapsedText(JOB.startedAt, '2026-11-24T10:00:00+00:00', now)).toBe('2 h');
  });
});
