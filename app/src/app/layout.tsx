import '@/globals';

import 'summit/styles.css';
import '@/assets/styles/theme.css';
import '@/assets/styles/tailwind.css';

import { fonts } from '@/service/fonts';
import { ThemeProvider } from '@/units/providers/theme-provider';

export default ({ children }: Children) => {
  return (
    <html lang="en" className={fonts}>
      <ThemeProvider>{children}</ThemeProvider>
    </html>
  );
};

export const metadata: Metadata = {
  title: 'Mass',
  description: ''
};
