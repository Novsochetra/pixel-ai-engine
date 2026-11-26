import { useState, type ReactNode } from 'react';
import { Link } from 'react-router';
import { Icon } from '@/components/icons';
import { Sheet } from '@/components/sheet/Sheet';
import { useShell } from './shell-context';
import { NARROW, useMediaQuery } from './use-media-query';
import './screen.css';

interface ScreenFrameProps {
  title: ReactNode;
  back?: { to: string; label: string };
  actions?: ReactNode;
  inspector: ReactNode;
  children: ReactNode;
}

// Toolbar on top, the work in the middle, the inspector on the right; a narrow screen opens the
// inspector as a sheet instead.
function BackLink({ to, label }: { to: string; label: string }) {
  return (
    <Link
      className="glass-button"
      to={to}
      aria-label={`Back to ${label}`}
      title={`Back to ${label}`}
    >
      <Icon name="previous" />
    </Link>
  );
}

export function ScreenFrame(props: ScreenFrameProps) {
  const { title, back, actions, inspector, children } = props;
  const { isInspectorShown, toggleInspector } = useShell();
  const isNarrow = useMediaQuery(NARROW);
  const [isSheetOpen, setSheetOpen] = useState(false);
  const isPanelShown = isInspectorShown && !isNarrow;

  return (
    <div className="screen" data-inspector={isPanelShown ? 'shown' : 'hidden'}>
      <header className="toolbar">
        <div className="toolbar__lead">
          {back ? <BackLink {...back} /> : null}
          <h1 className="toolbar__title">{title}</h1>
        </div>
        <div className="toolbar__actions">
          {actions}
          <button
            className="glass-button"
            type="button"
            aria-label="Inspector"
            title="Inspector"
            aria-pressed={isNarrow ? undefined : isInspectorShown}
            onClick={isNarrow ? () => setSheetOpen(true) : toggleInspector}
          >
            <Icon name="inspector" />
          </button>
        </div>
      </header>
      <div className="screen__content">{children}</div>
      <aside className="inspector" aria-label="Inspector" inert={!isPanelShown}>
        <div className="inspector__body">{isNarrow ? null : inspector}</div>
      </aside>
      {isNarrow ? (
        <Sheet title="Inspector" isOpen={isSheetOpen} onClosed={() => setSheetOpen(false)}>
          {inspector}
        </Sheet>
      ) : null}
    </div>
  );
}
