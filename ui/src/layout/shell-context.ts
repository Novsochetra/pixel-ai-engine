import { createContext, use } from 'react';

export interface ShellState {
  isInspectorShown: boolean;
  toggleInspector: () => void;
}

export const ShellContext = createContext<ShellState>({
  isInspectorShown: true,
  toggleInspector: () => {},
});

export const useShell = () => use(ShellContext);
