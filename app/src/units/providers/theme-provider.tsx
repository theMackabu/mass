import { ThemeHandle } from './theme-handle';

import { tw } from '@/service/utils';
import { getTheme } from '@/actions/get-theme';

export async function ThemeProvider({ children }: Children) {
  const theme = await getTheme();

  return (
    <body className={tw('bg-white text-black', 'dark:bg-zinc-950 dark:text-white')}>
      <ThemeHandle
        theme={theme}
        hasBackground={false}
        radius="medium"
        accentColor="gray"
        grayColor="sand"
      >
        {children}
      </ThemeHandle>
    </body>
  );
}
