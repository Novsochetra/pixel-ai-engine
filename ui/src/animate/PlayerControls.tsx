import { Icon } from '@/components/icons';
import { Stepper } from '@/components/stepper/Stepper';
import { FPS_RANGE, frameText } from './sprite-frames';
import type { SpritePlayerState } from './use-sprite-player';

function FrameButton({
  label,
  icon,
  onPress,
}: {
  label: string;
  icon: 'previous' | 'next';
  onPress: () => void;
}) {
  return (
    <button
      className="glass-button"
      type="button"
      aria-label={label}
      title={label}
      onClick={onPress}
    >
      <Icon name={icon} />
    </button>
  );
}

// Play and pause, a frame at a time either way, and the speed in frames a second.
export function PlayerControls({ player, count }: { player: SpritePlayerState; count: number }) {
  const playLabel = player.isPlaying ? 'Pause' : 'Play';

  return (
    <div className="player-controls">
      <div className="player-controls__transport" role="group" aria-label="Playback">
        <FrameButton label="Previous frame" icon="previous" onPress={player.previous} />
        <button
          className="glass-button"
          type="button"
          aria-label={playLabel}
          title={playLabel}
          onClick={player.toggle}
        >
          <Icon name={player.isPlaying ? 'pause' : 'play'} />
        </button>
        <FrameButton label="Next frame" icon="next" onPress={player.next} />
        <output className="player-controls__frame">{frameText(player.frame, count)}</output>
      </div>
      <div className="player-controls__speed">
        <Stepper
          label="Frames a second"
          value={player.fps}
          range={FPS_RANGE}
          onChange={player.setFps}
        />
      </div>
    </div>
  );
}
