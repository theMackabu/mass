'use client';

import { useRouter } from 'next/navigation';
import { useTheme } from '@/hooks/use-theme';
import { saveTheme } from '@/actions/save-theme';

import { Flex, Text, Button } from 'summit';

export const ThemeChanger = () => {
  const { refresh } = useRouter();
  const { resolved, theme, setTheme } = useTheme();

  const handleThemeChange = (event: React.MouseEvent<HTMLButtonElement>) => {
    const theme = event.currentTarget.dataset.theme as 'system' | 'light' | 'dark';

    setTheme(theme);
    void saveTheme(theme).then(() => refresh());
  };

  return (
    <Flex direction="column" gap="3" align="start">
      <Text size="4" weight="medium">
        Your current theme is {resolved}, using {theme}
      </Text>

      <Flex direction="column" gap="2" align="start">
        <Button variant="soft" data-theme="dark" onClick={handleThemeChange}>
          Set to dark
        </Button>
        <Button variant="soft" data-theme="light" onClick={handleThemeChange}>
          Set to light
        </Button>
        <Button variant="soft" data-theme="system" onClick={handleThemeChange}>
          Set to system
        </Button>
      </Flex>
    </Flex>
  );
};
