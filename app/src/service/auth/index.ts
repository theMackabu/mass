import { db } from '@/service/db';
import { betterAuth } from 'better-auth';
import { username } from 'better-auth/plugins';
import { nextCookies } from 'better-auth/next-js';
import { drizzleAdapter } from 'better-auth/adapters/drizzle';
import { jwt, organization, apiKey } from 'better-auth/plugins';

export const auth = betterAuth({
  emailAndPassword: { enabled: true },
  advanced: { cookiePrefix: 'mass' },
  database: drizzleAdapter(db, { provider: 'pg' }),

  user: {
    additionalFields: {
      theme: { type: 'string', input: true }
    }
  },

  session: {
    cookieCache: {
      enabled: true,
      maxAge: 5 * 60
    }
  },

  plugins: [jwt(), username(), organization(), apiKey({ enableMetadata: true }), nextCookies()]
});
