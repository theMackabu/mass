import type { ComponentType, PropsWithChildren } from 'react';

declare global {
  type ReactNode = React.ReactNode;
  type Component<T = unknown> = ComponentType<T>;
  type Children<P = unknown> = PropsWithChildren<P>;
  type NonNullableChildren<P = unknown> = P & { children: ReactNode };
}
