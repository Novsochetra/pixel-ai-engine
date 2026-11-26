import type { ReactNode } from 'react';
import { Icon, type IconName } from '@/components/icons';
import './empty-state.css';

interface EmptyStateProps {
  icon: IconName;
  title: string;
  children: ReactNode;
}

export function EmptyState({ icon, title, children }: EmptyStateProps) {
  return (
    <div className="empty-state">
      <span className="empty-state__icon">
        <Icon name={icon} size="large" />
      </span>
      <h2 className="empty-state__title">{title}</h2>
      <p className="empty-state__text">{children}</p>
    </div>
  );
}
