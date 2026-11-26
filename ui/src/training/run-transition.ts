// The card and the run's own screen share these names, so a navigation morphs one into the other.
// Run names hold only letters, digits, - and _, which a view-transition-name allows as it is.
export const runTransitionName = (run: string, part: 'card' | 'title') => `run-${part}-${run}`;
