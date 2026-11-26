import { Icon } from '@/components/icons';

// An error stays until it is closed or the next Generate, as the HIG asks.
export function FormError({ message, onClose }: { message: string; onClose: () => void }) {
  return (
    <div className="form-error" role="alert">
      <span className="form-error__icon">
        <Icon name="warning" />
      </span>
      <p className="form-error__text">{message}</p>
      <button
        className="glass-button form-error__close"
        type="button"
        aria-label="Close the error"
        title="Close the error"
        onClick={onClose}
      >
        <Icon name="close" />
      </button>
    </div>
  );
}
