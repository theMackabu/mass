import { Fragment } from 'react';
import { Toaster } from '#/elements/toaster';
import { DevMenu } from '#/elements/dev-menu';
import { AppShell } from '#/elements/app-shell';
import { useVersionCheck } from '@/hooks/use-version-check';

export function Layout({ children }: Children) {
  useVersionCheck();

  return (
    <Fragment>
      <Toaster />
      <DevMenu />
      <AppShell>{children}</AppShell>
    </Fragment>
  );
}
