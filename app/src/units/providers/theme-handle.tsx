'use client';

import { Theme } from 'summit';
import { Toaster } from 'sonner';
import { useState, useEffect } from 'react';
import { ThemeContext } from '@/hooks/use-theme';

type ThemeProps = Children<{ theme: string }> & React.ComponentProps<typeof Theme>;

export function ThemeHandle({ children, theme: initialTheme, ...props }: ThemeProps) {
  const [resolved, setResolved] = useState(initialTheme as Themes);
  const [theme, setTheme] = useState(initialTheme as Themes | 'system');

  useEffect(() => {
    if (theme === 'system') {
      const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');

      const updateTheme = () => {
        const systemTheme = mediaQuery.matches ? 'dark' : 'light';
        document.documentElement.setAttribute('data-theme', systemTheme);
        setResolved(systemTheme);
      };

      updateTheme();
      mediaQuery.addEventListener('change', updateTheme);

      return () => mediaQuery.removeEventListener('change', updateTheme);
    } else {
      document.documentElement.setAttribute('data-theme', theme);
      setResolved(theme as Themes);
    }
  }, [theme]);

  return (
    <Theme appearance={resolved} {...props}>
      <Toaster theme={resolved} />
      <ThemeContext.Provider value={{ theme, resolved, setTheme }}>
        {children}
      </ThemeContext.Provider>
    </Theme>
  );
}
