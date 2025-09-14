'use server';

import { auth } from '@/service/auth';
import { headers } from 'next/headers';

export async function updateProject(id: string, key: string, kind: string) {
  return await auth.api.updateApiKey({
    body: {
      keyId: id,
      metadata: { kind, auth: key, status: 'offline' },
    },
    headers: await headers(),
  });
}
