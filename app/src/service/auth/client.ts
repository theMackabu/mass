import type { auth } from '@/service/auth';
import { createAuthClient } from 'better-auth/react';
import { inferAdditionalFields } from 'better-auth/client/plugins';
import { usernameClient, organizationClient, apiKeyClient } from 'better-auth/client/plugins';

export const authClient = createAuthClient({
  plugins: [
    usernameClient(),
    organizationClient(),
    apiKeyClient(),
    inferAdditionalFields<typeof auth>()
  ]
});

export const { signIn, signOut, signUp, useSession } = authClient;
