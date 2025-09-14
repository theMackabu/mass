import { createAuthClient } from 'better-auth/react';
import { organizationClient } from 'better-auth/client/plugins';

export const authClient = createAuthClient({
  plugins: [organizationClient()],
  baseURL: 'https://localhost:3000',
});

export const useAuth = () => authClient;

export const { signIn, signUp, useSession, updateUser } = authClient;
