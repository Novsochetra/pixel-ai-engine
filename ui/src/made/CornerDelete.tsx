import { Icon } from '@/components/icons';
import type { MadeTarget } from './made-client';

// A card's trash button sits beside its main button, not inside it: a button may not hold another.
export function CornerDelete({
  target,
  onDelete,
}: {
  target: MadeTarget;
  onDelete: (target: MadeTarget) => void;
}) {
  const label = `Delete ${target.title}`;

  return (
    <button
      className="glass-button made-delete"
      type="button"
      aria-label={label}
      title={label}
      onClick={() => onDelete(target)}
    >
      <Icon name="trash" />
    </button>
  );
}
