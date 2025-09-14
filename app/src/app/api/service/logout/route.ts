import { auth } from '@/service/auth';
import { getCookie } from '@/hooks/get-cookie';

export async function GET(req: Request) {
  const sessionCookie = getCookie(req);
  if (!sessionCookie) return Response.redirect(new URL('/login', req.url));

  const { success } = await auth.api.signOut({ headers: req.headers });
  if (success) return Response.redirect(new URL('/login', req.url));
}
