import { getSessionCookie } from 'better-auth/cookies';

export function getCookie(request: Request) {
  return getSessionCookie(request, { cookiePrefix: 'mass' });
}
