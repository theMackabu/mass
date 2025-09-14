import { createContext, useContext } from 'react';

type ThemeContextType = {
  resolved: Themes;
  theme: Themes | 'system';
  setTheme: (theme: Themes | 'system') => void;
};

export const ThemeContext = createContext<ThemeContextType | undefined>(undefined);

export function useTheme() {
  const context = useContext(ThemeContext);

  if (context === undefined) {
    throw new Error('useTheme must be used within a ThemeHandle');
  }

  return context;
}
