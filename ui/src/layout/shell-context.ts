import { useOutletContext } from 'react-router';

export interface ShellContext {
  isInspectorShown: boolean;
  toggleInspector: () => void;
}

export const useShell = () => useOutletContext<ShellContext>();
