import type { Metadata as MetaType } from 'next';

declare global {
  type Metadata = MetaType;
  type Themes = 'dark' | 'light';
  type Slug<T = unknown> = { params: Promise<{ slug: string } & T> };
  type Children<P = unknown> = Readonly<P & { children?: React.ReactNode | undefined }>;
}

export {};
