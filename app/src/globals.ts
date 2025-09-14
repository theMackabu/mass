import type { Metadata as MetaType } from 'next';

declare global {
  type Metadata = MetaType;
  type Themes = 'dark' | 'light';
  type Params<T = unknown> = { params: Promise<T> };
  type Children<P = unknown> = Readonly<P & { children?: React.ReactNode | undefined }>;
}

export {};
