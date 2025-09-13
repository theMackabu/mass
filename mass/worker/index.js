import { z } from 'https://esm.sh/zod@3';

import { StreamableHTTPTransport } from 'https://esm.sh/@hono/mcp';
import { McpServer } from 'https://esm.sh/@modelcontextprotocol/sdk/server/mcp';

const mcp = new McpServer({
  name: 'mass',
  version: MASS.config.version(),
});

// tool for testing
mcp.registerTool(
  'calculate-bmi',
  {
    title: 'BMI Calculator',
    description: 'Calculate Body Mass Index',
    inputSchema: {
      weightKg: z.number(),
      heightM: z.number(),
    },
  },
  async ({ weightKg, heightM }) => ({
    content: [{ type: 'text', text: String(weightKg / (heightM * heightM)) }],
  }),
);

MASS.app.all('/socket', async c => {
  const transport = new StreamableHTTPTransport();
  await mcp.connect(transport);

  return transport.handleRequest(c);
});

Deno.serve({ port: MASS.config.port() }, MASS.app.fetch);
