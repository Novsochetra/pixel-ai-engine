import { useLayoutEffect, useRef, useState, type ReactNode } from 'react';
import { useLocation, useNavigationType } from 'react-router';
import { LayerContext } from './layer-context';
import {
  advanceStack,
  createStack,
  frontAndBack,
  settleStack,
  type StackModel,
} from './stack-model';
import { playMove } from './stack-motion';
import './stack.css';

type LayerRole = 'top' | 'front' | 'back' | 'hidden';

function roleOf(stack: StackModel, path: string): LayerRole {
  const pair = frontAndBack(stack);

  if (pair?.front === path) {
    return 'front';
  }

  if (pair) {
    return pair.back === path ? 'back' : 'hidden';
  }

  return stack.top === path ? 'top' : 'hidden';
}

// The stack follows the route: a move adds the screen arriving, plays on the two layers, then
// settles. A push or pop puts the focus on the screen arrived at, as a page load would; a swap
// leaves it in the sidebar or tab bar it came from.
function useStackMoves(path: string) {
  const navigationType = useNavigationType();
  const [stack, setStack] = useState(() => createStack(path));
  const layers = useRef(new Map<string, HTMLElement>());

  if (stack.top !== path) {
    setStack(advanceStack(stack, path, navigationType));
  }

  useLayoutEffect(() => {
    const pair = frontAndBack(stack);
    const front = pair && layers.current.get(pair.front);
    const back = pair && layers.current.get(pair.back);

    if (!front || !back || stack.move === 'none') {
      return undefined;
    }

    const move = playMove(stack.move, { front, back });

    move.finished.then(() => {
      setStack((current) => (current.id === stack.id ? settleStack(current) : current));
      if (stack.move !== 'swap') {
        layers.current.get(stack.top)?.focus({ preventScroll: true });
      }
    });

    return move.cancel;
  }, [stack]);

  return { stack, layers };
}

interface ScreenStackProps {
  renderScreen: (path: string) => ReactNode;
}

// Each screen is a live layer, so motion never waits on a picture of it and input is never held:
// the screen arrived at answers at once, while the one leaving is inert and lets clicks through.
export function ScreenStack({ renderScreen }: ScreenStackProps) {
  const { pathname } = useLocation();
  const { stack, layers } = useStackMoves(pathname);

  return (
    <div className="screen-stack">
      {stack.layers.map((path) => {
        const role = roleOf(stack, path);
        const isTop = path === stack.top;

        return (
          <section
            className={`screen-layer screen-layer--${role}`}
            key={path}
            ref={(element) => {
              if (element) {
                layers.current.set(path, element);
              } else {
                layers.current.delete(path);
              }
            }}
            tabIndex={-1}
            inert={!isTop}
            aria-hidden={isTop ? undefined : true}
          >
            <LayerContext value={{ isTop }}>{renderScreen(path)}</LayerContext>
          </section>
        );
      })}
    </div>
  );
}
