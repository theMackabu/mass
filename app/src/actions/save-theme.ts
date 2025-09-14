'use server';

import { auth } from '@/service/auth';
import { headers } from 'next/headers';

export async function saveTheme(theme: 'system' | 'light' | 'dark') {
  await auth.api.updateUser({
    body: { theme },
    headers: await headers()
  });
}
