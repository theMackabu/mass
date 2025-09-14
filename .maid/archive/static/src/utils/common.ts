import { toast } from 'sonner';
import { useLocation } from 'wouter';
import { twMerge } from 'tailwind-merge';
import { clsx, type ClassValue } from 'clsx';
import { useEffect, useInsertionEffect, useRef } from 'react';

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function capitalize(str: string | null | undefined) {
  if (!str || typeof str !== 'string') return '';
  return str.charAt(0).toUpperCase() + str.slice(1);
}

export function displayError(callback: (success: boolean) => void, error?: string) {
  toast.error(error ? capitalize(error) : 'Unexpected error during action.');
  callback(false);
}

export function navigateTo(path: string, callback?: () => void, deps?: React.DependencyList) {
  const [_, navigate] = useLocation();
  const redirect = useEvent(() => navigate(path));

  useEffect(() => {
    redirect();
    callback?.();
    // biome-ignore lint/correctness/useExhaustiveDependencies: redirect is stable due to useEvent
  }, deps || []);
}

export function useEvent<T extends (...args: never[]) => unknown>(fn: T): T {
  const ref = useRef<[T, T]>([fn, ((...args: Parameters<T>) => ref.current[0](...args)) as T]);

  // useInsertionEffect executes marginally closer to the
  // correct timing for ref synchronization than useLayoutEffect on React 19.
  // see: https://github.com/facebook/react/pull/25881#issuecomment-1356244360
  useInsertionEffect(() => {
    ref.current[0] = fn;
  });

  return ref.current[1];
}

export function quickHash(input: string): string {
  let hash = 0;
  if (input.length === 0) return '0';

  for (let i = 0; i < input.length; i++) {
    const char = input.charCodeAt(i);
    hash = (hash << 5) - hash + char;
    hash |= 0;
  }

  return (hash >>> 0).toString(16);
}
