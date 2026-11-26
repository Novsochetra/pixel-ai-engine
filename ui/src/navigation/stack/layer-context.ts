import { createContext, use } from 'react';

export const LayerContext = createContext<{ isTop: boolean }>({ isTop: true });

// A screen left under the stack stays rendered, so its keys (⌘↩) are its own only while it is the
// one the route shows.
export const useIsTopScreen = () => use(LayerContext).isTop;
