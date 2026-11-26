import { Icon } from '@/components/icons';
import { canZoomIn, canZoomOut, zoomIn, zoomOut, zoomText } from './pixel-scale';

export function ZoomControls({
  scale,
  onZoom,
}: {
  scale: number;
  onZoom: (scale: number) => void;
}) {
  return (
    <div className="zoom-controls" role="group" aria-label="Zoom">
      <button
        className="glass-button"
        type="button"
        aria-label="Zoom out"
        title="Zoom out"
        disabled={!canZoomOut(scale)}
        onClick={() => onZoom(zoomOut(scale))}
      >
        <Icon name="minus" />
      </button>
      <output className="zoom-controls__value" aria-live="polite">
        {zoomText(scale)}
      </output>
      <button
        className="glass-button"
        type="button"
        aria-label="Zoom in"
        title="Zoom in"
        disabled={!canZoomIn(scale)}
        onClick={() => onZoom(zoomIn(scale))}
      >
        <Icon name="plus" />
      </button>
    </div>
  );
}
