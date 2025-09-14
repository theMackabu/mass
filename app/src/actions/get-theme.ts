'use server';

import { getSession } from '@/actions/get-session';

export async function getTheme() {
  const { user } = await getSession();
  return (user?.theme as 'system' | 'light' | 'dark') ?? 'system';
}
