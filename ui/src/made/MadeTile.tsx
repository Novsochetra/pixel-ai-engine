import { useState, type ReactNode } from 'react';
import { CornerDelete } from './CornerDelete';
import type { MadeTarget } from './made-client';
import { useHoverFrames } from './use-hover-frames';
import './made-grid.css';

export type TileArt = (frame: number, onCount: (count: number) => void) => ReactNode;

interface MadeTileProps {
  title: string;
  subtitle: string;
  target: MadeTarget;
  fps: number;
  art: TileArt;
  onOpen: () => void;
  onDelete: (target: MadeTarget) => void;
}

// One made thing in a grid: its first frame still, playing frame by frame under the pointer. The
// art says how many frames it has once its picture is in.
export function MadeTile({ title, subtitle, target, fps, art, onOpen, onDelete }: MadeTileProps) {
  const [count, setCount] = useState(1);
  const frames = useHoverFrames(count, fps);

  return (
    <li className="made-item made-tile" {...frames.hover}>
      <button className="made-tile__open" type="button" onClick={onOpen}>
        <span className="made-tile__art pixel-art" data-playing={frames.isPlaying}>
          {art(frames.frame, setCount)}
        </span>
        <span className="made-tile__title" title={title}>
          {title}
        </span>
        <span className="made-tile__subtitle">{subtitle}</span>
      </button>
      <CornerDelete target={target} onDelete={onDelete} />
    </li>
  );
}

export function MadeGrid({ label, children }: { label: string; children: ReactNode }) {
  return (
    <ul className="made-grid" aria-label={label}>
      {children}
    </ul>
  );
}
