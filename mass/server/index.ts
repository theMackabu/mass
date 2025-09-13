import { Hono } from 'hono';
import { logger } from 'hono/logger';

const app = new Hono();

app.use(logger());

app.get('/', c => {
  return c.json({ pid: MASS.pid() });
});

export default app;
