import * as schema from '@/service/db/schema';
import { DATABASE_URL } from '@/service/env';
import { drizzle } from 'drizzle-orm/node-postgres';

export const db = drizzle({
  schema,
  casing: 'snake_case',
  connection: DATABASE_URL
});
