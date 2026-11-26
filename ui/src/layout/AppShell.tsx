import { useState, ViewTransition } from 'react';
import { Outlet } from 'react-router';
import { JobStatus } from '@/jobs/JobStatus';
import { Sidebar } from './Sidebar';
import { TabBar } from './TabBar';
import type { ShellContext } from './shell-context';
import '@/styles/transitions.css';
import './shell.css';

export function AppShell() {
  const [isInspectorShown, setInspectorShown] = useState(true);
  const context: ShellContext = {
    isInspectorShown,
    toggleInspector: () => setInspectorShown((shown) => !shown),
  };

  // The router navigates in a React Transition, so each change of screen animates in the boundary.
  return (
    <div className="shell">
      <Sidebar />
      <ViewTransition>
        <main className="shell__main">
          <Outlet context={context} />
        </main>
      </ViewTransition>
      <JobStatus placement="floating" />
      <TabBar />
    </div>
  );
}
