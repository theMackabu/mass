#!/usr/bin/env node

/**
 * MCP Server for GitHub Repository
 * 
 * This server provides MCP tools for interacting with a cloned GitHub repository.
 * It dynamically loads and exposes tools based on the repository structure.
 */

import { Server } from '@modelcontextprotocol/sdk/server/index.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
} from '@modelcontextprotocol/sdk/types.js';
import express from 'express';
import cors from 'cors';
import helmet from 'helmet';
import dotenv from 'dotenv';
import { readFileSync, existsSync } from 'fs';
import { join, dirname } from 'path';
import { fileURLToPath } from 'url';

// Load environment variables
dotenv.config();

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

// Load MCP tools configuration
let mcpTools = [];
let documentation = '';

try {
  // Try to load generated MCP tools from the repository
  const toolsPath = join(process.cwd(), 'mcp_tools.json');
  const docsPath = join(process.cwd(), 'documentation.md');
  
  if (existsSync(toolsPath)) {
    mcpTools = JSON.parse(readFileSync(toolsPath, 'utf8'));
    console.log(`✅ Loaded ${mcpTools.length} MCP tools from mcp_tools.json`);
  }
  
  if (existsSync(docsPath)) {
    documentation = readFileSync(docsPath, 'utf8');
    console.log(`✅ Loaded documentation (${documentation.length} chars)`);
  }
} catch (error) {
  console.warn('⚠️  Could not load MCP tools configuration:', error.message);
  console.log('Using default tools...');
  
  // Default tools if no configuration is found
  mcpTools = [
    {
      name: "analyze-repository",
      title: "Analyze Repository",
      description: "Analyze the current repository structure and contents",
      input_schema: {},
      category: "analysis"
    },
    {
      name: "list-files",
      title: "List Files",
      description: "List files in the repository",
      input_schema: {
        "path": "string"
      },
      category: "filesystem"
    }
  ];
}

// Create MCP server
const server = new Server(
  {
    name: "github-repo-mcp-server",
    version: "1.0.0",
  },
  {
    capabilities: {
      tools: {},
    },
  }
);

// List available tools
server.setRequestHandler(ListToolsRequestSchema, async () => {
  return {
    tools: mcpTools.map(tool => ({
      name: tool.name,
      description: tool.description,
      inputSchema: tool.input_schema,
    })),
  };
});

// Handle tool calls
server.setRequestHandler(CallToolRequestSchema, async (request) => {
  const { name, arguments: args } = request.params;
  
  try {
    switch (name) {
      case "analyze-repository":
        return {
          content: [
            {
              type: "text",
              text: `Repository Analysis:\n- Total MCP Tools: ${mcpTools.length}\n- Documentation: ${documentation ? 'Available' : 'Not found'}\n- Working Directory: ${process.cwd()}`
            }
          ]
        };
        
      case "list-files":
        const path = args?.path || '.';
        const fs = await import('fs');
        const files = fs.readdirSync(path);
        return {
          content: [
            {
              type: "text",
              text: `Files in ${path}:\n${files.join('\n')}`
            }
          ]
        };
        
      default:
        // Try to find and execute the tool
        const tool = mcpTools.find(t => t.name === name);
        if (tool) {
          return {
            content: [
              {
                type: "text",
                text: `Executing tool: ${tool.title}\nDescription: ${tool.description}\nCategory: ${tool.category}\n\nThis tool would execute: ${tool.implementation_hint || 'Tool implementation not available'}`
              }
            ]
          };
        } else {
          throw new Error(`Tool '${name}' not found`);
        }
    }
  } catch (error) {
    return {
      content: [
        {
          type: "text",
          text: `Error executing tool '${name}': ${error.message}`
        }
      ],
      isError: true
    };
  }
});

// Start the server
async function main() {
  const transport = new StdioServerTransport();
  await server.connect(transport);
  console.log('🚀 MCP Server started');
}

// Also provide HTTP API for web access
const app = express();
app.use(helmet());
app.use(cors());
app.use(express.json());

// Health check
app.get('/health', (req, res) => {
  res.json({
    status: 'healthy',
    tools: mcpTools.length,
    documentation: documentation ? 'available' : 'not found'
  });
});

// List tools
app.get('/tools', (req, res) => {
  res.json(mcpTools);
});

// Get documentation
app.get('/docs', (req, res) => {
  res.type('text/markdown');
  res.send(documentation || '# No documentation available');
});

// Execute tool
app.post('/tools/:name', async (req, res) => {
  const { name } = req.params;
  const args = req.body;
  
  try {
    const tool = mcpTools.find(t => t.name === name);
    if (!tool) {
      return res.status(404).json({ error: 'Tool not found' });
    }
    
    // For now, just return tool info
    res.json({
      tool: tool,
      args: args,
      message: 'Tool execution would happen here'
    });
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

const port = process.env.PORT || 3000;
app.listen(port, () => {
  console.log(`🌐 HTTP API available at http://localhost:${port}`);
  console.log(`📚 Documentation: http://localhost:${port}/docs`);
  console.log(`🛠️  Tools: http://localhost:${port}/tools`);
});

// Start MCP server
main().catch(console.error);
