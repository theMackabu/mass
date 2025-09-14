import 'dotenv/config';
import { defineConfig } from 'drizzle-kit';

export default defineConfig({
  out: './drizzle',
  dialect: 'postgresql',
  schema: './src/service/db/schema',
  dbCredentials: {
    url: process.env.DATABASE_URL!
  }
});
