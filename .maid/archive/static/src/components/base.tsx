import { Index } from '#/pages/index';
import { Login } from '#/pages/login';

import { Layout } from '#/layout';
import { Router, Route, Switch } from 'wouter';
import { NuqsAdapter } from 'nuqs/adapters/react';
import { SuspenseWithPrevious } from '#/elements/suspense';

import { buildProvidersTree } from '#/elements/provider-tree';
import { useBrowserLocation } from 'wouter/use-browser-location';

const AppProviders = buildProvidersTree([
  [NuqsAdapter],
  [SuspenseWithPrevious],
  [Layout],
  [Router, { hook: useBrowserLocation }],
  [Switch],
]);

export function AppView() {
  return (
    <AppProviders>
      <Route path="/" component={Index} />
      <Route path="/login" component={Login} />
    </AppProviders>
  );
}
