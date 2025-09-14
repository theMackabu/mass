'use server';

import { auth } from '@/service/auth';
import { headers } from 'next/headers';

export async function getProject(id: string) {
  return await auth.api.getApiKey({
    query: { id },
    headers: await headers(),
  });
}
