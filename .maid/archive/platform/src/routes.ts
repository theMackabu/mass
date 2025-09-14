import { Hono } from 'hono';
import { APP_PORT } from '@/env';
import type { Session, User } from 'better-auth';

import { auth } from '@/auth';
import { cors } from 'hono/cors';
import { compress } from '@hono/bun-compress';

const app = new Hono<{
  Variables: {
    user: User | null;
    session: Session | null;
  };
}>();

app.use(compress({ encoding: 'gzip' }));

app.use(
  cors({
    origin: '*', // replace with our origin later
    allowHeaders: ['Content-Type', 'Authorization'],
    allowMethods: ['GET', 'POST', 'OPTIONS'],
    exposeHeaders: ['Content-Length'],
    maxAge: 600,
    credentials: true,
  }),
);

app.use('*', async (c, next) => {
  const session = await auth.api.getSession({ headers: c.req.raw.headers });

  if (!session) {
    c.set('user', null);
    c.set('session', null);
    return next();
  }

  c.set('user', session.user);
  c.set('session', session.session);
  return next();
});

app.notFound(c => {
  return c.text('not found :(', 404);
});

app.onError((error, c) => {
  console.error(error);
  return c.text('something went wrong :(', 500);
});

app.on(['POST', 'GET'], '/auth/*', c => {
  return auth.handler(c.req.raw);
});

app.get('/session', c => {
  const session = c.get('session');
  const user = c.get('user');

  if (!user) return c.body(null, 401);
  return c.json({ session, user });
});

export default {
  port: APP_PORT,
  fetch: app.fetch,
};
