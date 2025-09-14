import { Inter, Geist_Mono } from 'next/font/google';

const inter = Inter({
  variable: '--font-geist-sans',
  subsets: ['latin']
});

const mono = Geist_Mono({
  variable: '--font-geist-mono',
  subsets: ['latin']
});

export const fonts = `${inter.variable} ${mono.variable} antialiased`;
