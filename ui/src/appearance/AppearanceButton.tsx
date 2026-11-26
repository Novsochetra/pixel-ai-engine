import { Icon } from '@/components/icons';
import { useAppearance } from './use-appearance';

export function AppearanceButton() {
  const { appearance, toggle } = useAppearance();
  const label = appearance === 'dark' ? 'Use light appearance' : 'Use dark appearance';

  return (
    <button
      className="glass-button"
      type="button"
      aria-label={label}
      title={label}
      onClick={toggle}
    >
      <Icon name={appearance === 'dark' ? 'sun' : 'moon'} />
    </button>
  );
}
