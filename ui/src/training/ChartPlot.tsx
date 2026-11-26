import { stepText } from './chart-readout';
import { linePath, tickDecimals, type Box, type Point, type Scale } from './loss-chart';
import type { useChartPointer } from './use-chart-pointer';

interface PlotProps {
  smooth: readonly Point[];
  val: readonly Point[];
  scale: Scale;
  box: Box;
}

const MARKER_RADIUS = 4;
const TICK_GAP = 8;

function Axes({ scale, box }: Omit<PlotProps, 'smooth' | 'val'>) {
  const decimals = tickDecimals(scale.values);

  return (
    <g className="loss-chart__axes" aria-hidden="true">
      {scale.values.map((value) => (
        <g key={value}>
          <line x1={box.left} x2={box.width - box.right} y1={scale.y(value)} y2={scale.y(value)} />
          <text
            x={box.left - TICK_GAP}
            y={scale.y(value)}
            textAnchor="end"
            dominantBaseline="middle"
          >
            {value.toFixed(decimals)}
          </text>
        </g>
      ))}
      {scale.steps.map((step, i) => (
        <text
          key={step}
          x={scale.x(step)}
          y={box.height - TICK_GAP}
          textAnchor={i === scale.steps.length - 1 ? 'end' : 'middle'}
        >
          {stepText(step)}
        </text>
      ))}
    </g>
  );
}

type Pointer = ReturnType<typeof useChartPointer>;

function Crosshair({ point, scale, box }: { point: Point; scale: Scale; box: Box }) {
  const x = scale.x(point[0]);

  return (
    <g aria-hidden="true">
      <line
        className="loss-chart__crosshair"
        x1={x}
        x2={x}
        y1={box.top}
        y2={box.height - box.bottom}
      />
      <circle className="loss-chart__marker" cx={x} cy={scale.y(point[1])} r={MARKER_RADIUS} />
    </g>
  );
}

// The loss behind, the val loss over it with a dot at each check; the crosshair reads a step.
export function ChartPlot({
  smooth,
  val,
  scale,
  box,
  pointer,
  label,
}: PlotProps & { pointer: Pointer; label: string }) {
  const active = pointer.index === null ? null : smooth[pointer.index];

  return (
    <svg
      className="loss-chart__plot"
      width={box.width}
      height={box.height}
      role="img"
      aria-label={label}
      tabIndex={0}
      onPointerMove={pointer.onPointerMove}
      onPointerLeave={pointer.clear}
      onFocus={pointer.onFocus}
      onBlur={pointer.clear}
      onKeyDown={pointer.onKeyDown}
    >
      <Axes scale={scale} box={box} />
      <path className="loss-chart__loss" d={linePath(smooth, scale)} />
      <path className="loss-chart__val" d={linePath(val, scale)} />
      {val.map(([step, value]) => (
        <circle
          className="loss-chart__check"
          key={step}
          cx={scale.x(step)}
          cy={scale.y(value)}
          r={MARKER_RADIUS}
        />
      ))}
      {active ? <Crosshair point={active} scale={scale} box={box} /> : null}
    </svg>
  );
}
