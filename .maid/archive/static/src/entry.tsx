import '@/assets/styles.css';

import '@radix-ui/themes/tokens/base.css';
import '@radix-ui/themes/tokens/colors/red.css';
import '@radix-ui/themes/tokens/colors/green.css';

import '@radix-ui/themes/components.css';
import '@radix-ui/themes/utilities.css';

import { createRoot } from 'react-dom/client';
import { reactScan } from '@/utils/react-scan';

import { AppView } from '#/base';
import { StrictMode } from 'react';
import { ThemeProvider } from '@/providers/theme';

if (import.meta.env.DEV) reactScan();

const container = document.getElementById('entry');
const entryPoint = createRoot(container as HTMLElement);

entryPoint.render(
  <StrictMode>
    <ThemeProvider>
      <AppView />
    </ThemeProvider>
  </StrictMode>,
);
