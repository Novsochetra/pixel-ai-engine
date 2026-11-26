import { useEffect, useState } from 'react';

// Searching millions of captions takes a moment, so wait until the typing pauses.
export function useDebounced<Value>(value: Value, delayMs: number): Value {
  const [settled, setSettled] = useState(value);

  useEffect(() => {
    const timer = setTimeout(() => setSettled(value), delayMs);

    return () => clearTimeout(timer);
  }, [value, delayMs]);

  return settled;
}
