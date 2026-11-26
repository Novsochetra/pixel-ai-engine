import { useState } from 'react';
import { Outlet } from 'react-router';
import { JobStatus } from '@/jobs/JobStatus';
import { Sidebar } from './Sidebar';
import { TabBar } from './TabBar';
import type { ShellContext } from './shell-context';
import './shell.css';

export function AppShell() {
  const [isInspectorShown, setInspectorShown] = useState(true);
  const context: ShellContext = {
    isInspectorShown,
    toggleInspector: () => setInspectorShown((shown) => !shown),
  };

  return (
    <div className="shell">
      <Sidebar />
      <main className="shell__main">
        <Outlet context={context} />
      </main>
      <JobStatus placement="floating" />
      <TabBar />
    </div>
  );
}
