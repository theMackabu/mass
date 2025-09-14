import { getCookie } from '@/hooks/get-cookie';

export async function GET(req: Request) {
  const sessionCookie = getCookie(req);
  return Response.json({ sessionCookie });
}
