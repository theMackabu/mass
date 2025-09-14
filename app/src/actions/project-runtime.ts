'use server';

import { auth } from '@/service/auth';
import { headers } from 'next/headers';

export async function projectRuntime(id: string, status: string) {
  const data = await auth.api.getApiKey({
    query: { id },
    headers: await headers(),
  });

  return await auth.api.updateApiKey({
    body: {
      keyId: id,
      metadata: { ...data.metadata, status },
    },
    headers: await headers(),
  });
}
