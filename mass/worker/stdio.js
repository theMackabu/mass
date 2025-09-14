// Alternative stdio transport version for direct editor integration
import { StdioServerTransport } from 'https://esm.sh/@modelcontextprotocol/sdk/server/stdio';
import { McpServer, ResourceTemplate } from 'https://esm.sh/@modelcontextprotocol/sdk/server/mcp';
import { z } from 'https://esm.sh/zod@3';

// Create MCP server for stdio transport
const server = new McpServer({
  name: 'mass-stdio',
  version: '0.0.1',
});

// Workspace root
const WORKSPACE_ROOT = Deno.env.get('WORKSPACE_ROOT') || Deno.cwd();

// Helper functions (duplicated for standalone stdio version)
function resolveWithinRoot(workspaceRoot, relPath) {
  const cleaned = (relPath || '').replace(/^\/+/, '').replace(/\\/g, '/');
  const resolved = `${workspaceRoot}/${cleaned}`.replace(/\/+/g, '/');
  
  const normalizedWorkspace = workspaceRoot.replace(/\/+$/, '');
  const normalizedResolved = resolved.replace(/\/+$/, '');
  
  if (!normalizedResolved.startsWith(normalizedWorkspace)) {
    throw new Error('Path outside workspace root');
  }
  
  return resolved;
}

function isTextFile(filePath) {
  const textExtensions = ['.ts', '.tsx', '.js', '.jsx', '.json', '.md', '.txt', 
                         '.yml', '.yaml', '.toml', '.py', '.rs', '.go', '.java',
                         '.css', '.scss', '.html', '.svg', '.xml', '.sh', '.bash'];
  const ext = filePath.toLowerCase().substring(filePath.lastIndexOf('.'));
  return textExtensions.includes(ext);
}

function shouldSkipFile(name, path) {
  const skipPatterns = [
    /^\./,                    // Hidden files
    /^node_modules$/,        // Dependencies
    /^target$/,
    /^__pycache__$/,
    /^\.venv$/,
    /^venv$/,
    /^build$/,
    /^dist$/,
    /\.DS_Store$/,           // OS files
    /Thumbs\.db$/,
    /\.log$/,                // Logs
    /\.tmp$/,
    /\.pyc$/,                // Compiled
    /\.class$/,
  ];
  
  return skipPatterns.some(pattern => pattern.test(name) || pattern.test(path));
}

// Register the same repository resource
server.registerResource(
  "repo",
  new ResourceTemplate("repo://{path}", {
    list: { path: "" },
  }),
  {
    title: "Repository",
    description: "Browse and read files from the current repository workspace",
  },
  async (uri, { path }) => {
    try {
      const fullPath = resolveWithinRoot(WORKSPACE_ROOT, path || '');
      const stat = await Deno.stat(fullPath);
      
      if (stat.isDirectory) {
        const entries = [];
        for await (const entry of Deno.readDir(fullPath)) {
          if (shouldSkipFile(entry.name, path ? `${path}/${entry.name}` : entry.name)) {
            continue;
          }
          
          const entryPath = path ? `${path}/${entry.name}` : entry.name;
          const entryFullPath = `${fullPath}/${entry.name}`;
          
          let entryStat;
          try {
            entryStat = await Deno.stat(entryFullPath);
          } catch {
            continue;
          }
          
          entries.push({
            name: entry.name,
            path: entryPath,
            isDirectory: entry.isDirectory,
            size: entryStat.size,
            modified: entryStat.mtime?.toISOString(),
            uri: `repo://${entryPath}`
          });
        }
        
        return {
          contents: [{
            uri: uri.href,
            mimeType: 'application/json',
            text: JSON.stringify(entries, null, 2)
          }]
        };
      }
      
      if (stat.isFile) {
        const data = await Deno.readFile(fullPath);
        
        if (isTextFile(fullPath)) {
          const text = new TextDecoder().decode(data);
          return {
            contents: [{
              uri: uri.href,
              mimeType: 'text/plain',
              text
            }]
          };
        } else {
          const uint8Array = new Uint8Array(data);
          const binaryString = Array.from(uint8Array, byte => String.fromCharCode(byte)).join('');
          const base64 = btoa(binaryString);
          
          return {
            contents: [{
              uri: uri.href,
              mimeType: 'application/octet-stream',
              blob: base64
            }]
          };
        }
      }
      
      throw new Error(`Invalid file type: ${path || 'root'}`);
      
    } catch (error) {
      throw new Error(`Failed to read resource: ${error.message}`);
    }
  }
);

// Add basic tools for stdio version
server.registerTool(
  'read-file',
  {
    title: 'Read Repository File',
    description: 'Read a specific file from the current repository',
    inputSchema: {
      filePath: z.string().describe('Path to file relative to repository root'),
    },
  },
  async ({ filePath }) => {
    try {
      const fullPath = resolveWithinRoot(WORKSPACE_ROOT, filePath);
      const stat = await Deno.stat(fullPath);
      
      if (!stat.isFile) {
        throw new Error(`Path is not a file: ${filePath}`);
      }
      
      const data = await Deno.readFile(fullPath);
      
      if (isTextFile(fullPath)) {
        const content = new TextDecoder().decode(data);
        return {
          content: [{
            type: 'text',
            text: content
          }]
        };
      } else {
        return {
          content: [{
            type: 'text',
            text: `Binary file: ${filePath} (${data.length} bytes)`
          }]
        };
      }
    } catch (error) {
      return {
        content: [{
          type: 'text',
          text: `Error reading file: ${error.message}`
        }]
      };
    }
  }
);

// Use stdio transport
const transport = new StdioServerTransport();

async function main() {
  await server.connect(transport);
}

if (import.meta.main) {
  main().catch((error) => {
    console.error('Server error:', error);
    Deno.exit(1);
  });
}