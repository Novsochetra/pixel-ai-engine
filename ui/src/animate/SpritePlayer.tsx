import { useState } from 'react';
import { Icon } from '@/components/icons';
import { Picker } from '@/components/picker/Picker';
import { Segmented } from '@/components/segmented/Segmented';
import { ZoomControls } from '@/library/ZoomControls';
import type { AnimatedRun, Clip } from './animate-client';
import { actionText, clipActions, clipText, clipViews, findClip, viewText } from './clip-view';
import { PlayerControls } from './PlayerControls';
import { SheetFrame, type SheetMeasure } from './SheetFrame';
import { clipFps } from './sprite-frames';
import { useSpritePlayer } from './use-sprite-player';
import './player.css';

interface PlayerProps {
  run: AnimatedRun;
  clip: Clip;
  onChoose: (clip: Clip) => void;
}

// The run's other clips, by view and by action; a run of one clip has nothing to choose.
function ClipChoices({ run, clip, onChoose }: PlayerProps) {
  const views = clipViews(run).map((view) => ({ value: view, label: viewText(view) }));
  const actions = clipActions(run).map((action) => ({ value: action, label: actionText(action) }));
  const choose = (view: string | null, action: string) => onChoose(findClip(run, view, action)!);

  return (
    <div className="sprite-player__choices">
      {views.length > 1 ? (
        <Segmented
          label="View"
          options={views}
          value={clip.view ?? ''}
          onChange={(view) => choose(view, clip.action)}
        />
      ) : null}
      {actions.length > 1 ? (
        <Picker
          label="Action"
          value={clip.action}
          options={actions}
          onChange={(action) => choose(clip.view, action)}
        />
      ) : null}
    </div>
  );
}

// A clip's sheet, played a frame at a time at whole-number zoom, with the files it came from. The
// player lives as long as its run, so another view of the clip keeps the speed, zoom and frame.
export function SpritePlayer({ run, clip, onChoose }: PlayerProps) {
  const [measure, setMeasure] = useState<SheetMeasure>({ count: Math.max(clip.kept, 1), fit: 1 });
  const [zoom, setZoom] = useState<number | null>(null);
  const player = useSpritePlayer(measure.count, clipFps(clip));

  return (
    <section className="sprite-player" aria-label="Player">
      <div className="sprite-player__stage pixel-art">
        <SheetFrame
          src={clip.sheet}
          alt={`${run.source}, ${clipText(clip)}`}
          kept={clip.kept}
          frame={player.frame}
          scale={zoom ?? undefined}
          onMeasure={setMeasure}
        />
      </div>
      <ClipChoices run={run} clip={clip} onChoose={onChoose} />
      <PlayerControls player={player} count={measure.count} />
      <div className="sprite-player__files">
        <ZoomControls scale={zoom ?? measure.fit} onZoom={setZoom} />
        <span className="sprite-player__links">
          <a
            className="pill-button pill-button--plain"
            href={clip.raw}
            target="_blank"
            rel="noreferrer"
          >
            Raw video
          </a>
          <a className="pill-button pill-button--tinted" href={clip.sheet} download>
            <Icon name="download" />
            Download sheet
          </a>
        </span>
      </div>
    </section>
  );
}
