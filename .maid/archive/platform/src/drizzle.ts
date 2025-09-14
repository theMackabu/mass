import * as schema from '#schema/';
import { DATABASE_URL } from '@/env';
import { drizzle } from 'drizzle-orm/node-postgres';

export const db = drizzle({
  schema,
  casing: 'snake_case',
  connection: DATABASE_URL,
});

export * as schema from '#schema/';
