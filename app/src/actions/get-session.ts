'use server';

import { auth } from '@/service/auth';
import { headers } from 'next/headers';

export async function getSession() {
  const session = await auth.api.getSession({
    headers: await headers()
  });

  if (!session) {
    return { user: null };
  }

  return session;
}
