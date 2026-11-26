import { useState } from 'react';
import { JobStatus } from '@/jobs/JobStatus';
import { ScreenRoutes } from '@/navigation/ScreenRoutes';
import { ScreenStack } from '@/navigation/stack/ScreenStack';
import { Sidebar } from './Sidebar';
import { TabBar } from './TabBar';
import { ShellContext, type ShellState } from './shell-context';
import './shell.css';

export function AppShell() {
  const [isInspectorShown, setInspectorShown] = useState(true);
  const shell: ShellState = {
    isInspectorShown,
    toggleInspector: () => setInspectorShown((shown) => !shown),
  };

  return (
    <ShellContext value={shell}>
      <div className="shell">
        <Sidebar />
        <main className="shell__main">
          <ScreenStack renderScreen={(path) => <ScreenRoutes path={path} />} />
        </main>
        <JobStatus placement="floating" />
        <TabBar />
      </div>
    </ShellContext>
  );
}
