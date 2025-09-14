'use server';

import { auth } from '@/service/auth';
import { headers } from 'next/headers';

export async function listProjects() {
  return await auth.api.listApiKeys({ headers: await headers() });
}
