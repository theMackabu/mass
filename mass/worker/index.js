import { z } from 'https://esm.sh/zod@3';

import { StreamableHTTPTransport } from 'https://esm.sh/@hono/mcp';
import { McpServer, ResourceTemplate } from 'https://esm.sh/@modelcontextprotocol/sdk/server/mcp';

// Import container orchestrator
const ContainerOrchestrator = (await import('../docker/orchestrator.js')).default;

// Helper functions for filesystem resource handling
function resolveWithinRoot(workspaceRoot, relPath) {
  // Normalize path and remove leading slashes
  const cleaned = (relPath || '').replace(/^\/+/, '').replace(/\\/g, '/');
  
  // Join with workspace root
  const resolved = `${workspaceRoot}/${cleaned}`.replace(/\/+/g, '/');
  
  // Ensure it doesn't escape workspace root
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

// Simple helper to run terminal commands
async function runCommand(cmd, args, cwd = WORKSPACE_ROOT) {
  try {
    const command = new Deno.Command(cmd, {
      args,
      cwd,
      stdout: "piped",
      stderr: "piped"
    });

    const child = command.spawn();
    const { code, stdout, stderr } = await child.output();
    
    const output = new TextDecoder().decode(stdout);
    const error = new TextDecoder().decode(stderr);
    
    return { code, output, error };
  } catch (err) {
    return { code: -1, output: "", error: err.message };
  }
}

// Get repository structure using tree command
async function getRepositoryTree(workspacePath) {
  try {
    const command = new Deno.Command("tree", {
      args: [
        "-a",           // Show hidden files
        "-I",           // Ignore patterns
        "node_modules|target|.git|__pycache__|.venv|venv|dist|build",
        "-L", "4",      // Max depth 4 levels
        "--dirsfirst",  // Directories first
        "-F",           // Add file type indicators
        workspacePath
      ],
      stdout: "piped",
      stderr: "piped"
    });

    const child = command.spawn();
    const { code, stdout, stderr } = await child.output();
    
    if (code === 0) {
      return new TextDecoder().decode(stdout);
    } else {
      // Fallback to ls if tree not available
      return await getRepositoryListing(workspacePath);
    }
  } catch (error) {
    console.warn("Tree command failed, using fallback:", error);
    return await getRepositoryListing(workspacePath);
  }
}

// Fallback directory listing if tree command not available
async function getRepositoryListing(workspacePath) {
  try {
    const command = new Deno.Command("find", {
      args: [
        workspacePath,
        "-type", "f",
        "-not", "-path", "*/node_modules/*",
        "-not", "-path", "*/target/*", 
        "-not", "-path", "*/.git/*",
        "-not", "-path", "*/__pycache__/*",
        "-maxdepth", "3"
      ],
      stdout: "piped",
      stderr: "piped"
    });

    const child = command.spawn();
    const { code, stdout } = await child.output();
    
    if (code === 0) {
      return new TextDecoder().decode(stdout);
    }
    
    return "Could not generate repository structure";
  } catch (error) {
    return `Error generating repository listing: ${error.message}`;
  }
}

// Create tar.gz archive of repository
async function createRepositoryArchive(repoId, workspacePath) {
  const timestamp = Date.now();
  const archiveName = `repo-${repoId}-${timestamp}.tar.gz`;
  const archivePath = `/tmp/${archiveName}`;
  
  try {
    const command = new Deno.Command("tar", {
      args: [
        "-czf", archivePath,
        "--exclude=node_modules",
        "--exclude=target", 
        "--exclude=.git",
        "--exclude=__pycache__",
        "--exclude=.venv",
        "--exclude=venv",
        "--exclude=dist",
        "--exclude=build",
        "--exclude=*.log",
        "-C", workspacePath,
        "."
      ],
      stdout: "piped",
      stderr: "piped"
    });

    const child = command.spawn();
    const { code, stderr } = await child.output();
    
    if (code !== 0) {
      const errorText = new TextDecoder().decode(stderr);
      throw new Error(`Tar command failed: ${errorText}`);
    }
    
    return archivePath;
  } catch (error) {
    throw new Error(`Failed to create repository archive: ${error.message}`);
  }
}

const mcp = new McpServer({
  name: 'mass',
  version: MASS.config.version(),
});

// Workspace root - default to current working directory
const WORKSPACE_ROOT = Deno.env.get('WORKSPACE_ROOT') || Deno.cwd();

// Register repository filesystem resource with proper ResourceTemplate
mcp.registerResource(
  "repo",
  new ResourceTemplate("repo://{path}", {
    list: { path: "" }, // Advertise repo root for discovery
  }),
  {
    title: "Repository",
    description: "Browse and read files from the current repository workspace",
  },
  async (uri, { path }) => {
    try {
      const fullPath = resolveWithinRoot(WORKSPACE_ROOT, path || '');
      
      // Check if path exists
      let stat;
      try {
        stat = await Deno.stat(fullPath);
      } catch (error) {
        throw new Error(`File not found: ${path || 'root'}`);
      }
      
      // Handle directories - return listing as JSON
      if (stat.isDirectory) {
        const entries = [];
        for await (const entry of Deno.readDir(fullPath)) {
          // Skip hidden files and common ignore patterns
          if (entry.name.startsWith('.') || 
              entry.name === 'node_modules' || 
              entry.name === 'target' ||
              entry.name === '__pycache__' ||
              entry.name === '.venv' ||
              entry.name === 'venv' ||
              entry.name === 'dist' ||
              entry.name === 'build') {
            continue;
          }
          
          const entryPath = path ? `${path}/${entry.name}` : entry.name;
          const entryFullPath = `${fullPath}/${entry.name}`;
          
          let entryStat;
          try {
            entryStat = await Deno.stat(entryFullPath);
          } catch {
            continue; // Skip if can't stat
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
      
      // Handle files - return content
      if (stat.isFile) {
        const data = await Deno.readFile(fullPath);
        
        // Return as text if it's a text file, otherwise as base64 blob
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
          // Binary file - return as base64 blob
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

// Repository storage system
const repositories = new Map();

// Container orchestrator instance
const orchestrator = new ContainerOrchestrator();

// Get repository tree structure
mcp.registerTool(
  'get-repo-tree',
  {
    title: 'Get Repository Tree Structure', 
    description: 'Get the file tree structure of the current repository using tree command',
    inputSchema: {},
  },
  async () => {
    try {
      const treeOutput = await getRepositoryTree(WORKSPACE_ROOT);
      
      return {
        content: [{
          type: 'text',
          text: treeOutput
        }]
      };
    } catch (error) {
      return {
        content: [{
          type: 'text',
          text: `Error getting repository tree: ${error.message}`
        }]
      };
    }
  }
);

// Create and analyze repository archive
mcp.registerTool(
  'analyze-repository',
  {
    title: 'Analyze Repository',
    description: 'Create tar.gz archive and analyze repository using Rust operations',
    inputSchema: {
      repoId: z.string().describe('Unique identifier for the repository'),
      projectName: z.string().optional().describe('Optional project name'),
      description: z.string().optional().describe('Optional project description'),
      maxFiles: z.number().optional().describe('Maximum important files to extract (default: 20)'),
    },
  },
  async ({ repoId, projectName, description, maxFiles = 20 }) => {
    try {
      // Get repository structure using tree command
      const treeOutput = await getRepositoryTree(WORKSPACE_ROOT);
      
      // Create tar.gz archive of repository
      const archivePath = await createRepositoryArchive(repoId, WORKSPACE_ROOT);
      
      // Extract and analyze using Rust operations
      const tempDir = `/tmp/mass-analysis-${repoId}-${Date.now()}`;
      const extractResult = await MASS.ops.op_extract_tar_gz(archivePath, tempDir);
      const analysis = await MASS.ops.op_analyze_repository(tempDir);
      const importantFiles = await MASS.ops.op_get_important_files(tempDir, maxFiles);
      
      // Store repository data
      repositories.set(repoId, {
        id: repoId,
        projectName,
        description,
        archivePath,
        treeStructure: treeOutput,
        analysis,
        importantFiles: importantFiles.split('\n---FILE_SEPARATOR---\n').filter(f => f.trim()),
        storedAt: new Date().toISOString(),
        workspacePath: WORKSPACE_ROOT,
      });

      // Trigger intelligent MCP analysis and generation using OpenAI
      const intelligentAnalysis = await callIntelligentAgent(repoId);
      
      // Clean up temp directory
      await MASS.ops.op_cleanup_temp_directory(tempDir);
      
      return {
        content: [{
          type: 'text',
          text: JSON.stringify({
            success: true,
            repoId,
            workspacePath: WORKSPACE_ROOT,
            archivePath,
            analysis,
            importantFilesCount: repositories.get(repoId).importantFiles.length,
            generatedTools: intelligentAnalysis.mcp_tools?.length || 0,
            apiEndpoints: intelligentAnalysis.codebase_analysis?.api_endpoints?.length || 0,
            serverTemplate: !!intelligentAnalysis.server_template,
            message: `Repository analyzed successfully. Generated ${intelligentAnalysis.mcp_tools?.length || 0} MCP tools and deployable server.`
          }, null, 2)
        }]
      };
    } catch (error) {
      return {
        content: [{
          type: 'text',
          text: JSON.stringify({
            success: false,
            error: error.message,
            repoId
          }, null, 2)
        }]
      };
    }
  }
);

// Store and process user repository (keep for external clients)
mcp.registerTool(
  'store-repository',
  {
    title: 'Store User Repository',
    description: 'Store entire user repository structure and files for MCP tool generation',
    inputSchema: {
      repoId: z.string().describe('Unique identifier for the repository'),
      files: z.record(z.string()).describe('Object mapping file paths to their content'),
      projectName: z.string().optional().describe('Optional project name'),
      description: z.string().optional().describe('Optional project description'),
    },
  },
  async ({ repoId, files, projectName, description }) => {
    try {
      // Store repository data
      repositories.set(repoId, {
        id: repoId,
        projectName,
        description,
        files,
        storedAt: new Date().toISOString(),
        fileStructure: analyzeFileStructure(files),
        apiEndpoints: extractApiEndpoints(files),
      });

      // Trigger MCP tool generation using Python agent
      const generatedTools = await callPythonAgent(repoId);
      
      return {
        content: [{
          type: 'text',
          text: JSON.stringify({
            success: true,
            repoId,
            filesStored: Object.keys(files).length,
            generatedTools: generatedTools.length,
            message: `Repository stored successfully. Generated ${generatedTools.length} MCP tools.`
          }, null, 2)
        }]
      };
    } catch (error) {
      return {
        content: [{
          type: 'text',
          text: JSON.stringify({
            success: false,
            error: error.message,
            repoId
          }, null, 2)
        }]
      };
    }
  }
);

// Generate Dockerfile for repository
mcp.registerTool(
  'generate-dockerfile',
  {
    title: 'Generate Dockerfile',
    description: 'Generate a Dockerfile for the stored repository using AI',
    inputSchema: {
      repoId: z.string().describe('Repository ID to generate Dockerfile for'),
    },
  },
  async ({ repoId }) => {
    try {
      const repo = repositories.get(repoId);
      if (!repo) {
        throw new Error(`Repository ${repoId} not found`);
      }

      const dockerfile = await generateDockerfile(repo);
      
      return {
        content: [{
          type: 'text',
          text: dockerfile
        }]
      };
    } catch (error) {
      return {
        content: [{
          type: 'text',
          text: `Error generating Dockerfile: ${error.message}`
        }]
      };
    }
  }
);

// List stored repositories with enhanced metadata
mcp.registerTool(
  'list-repositories',
  {
    title: 'List Stored Repositories',
    description: 'List all stored repositories and their detailed analysis metadata',
    inputSchema: {},
  },
  async () => {
    const repos = Array.from(repositories.values()).map(repo => ({
      id: repo.id,
      projectName: repo.projectName,
      description: repo.description,
      filesCount: Object.keys(repo.files).length,
      storedAt: repo.storedAt,
      apiEndpoints: repo.apiEndpoints?.length || 0,
      analysis: repo.analysis ? {
        projectType: repo.analysis.project_type,
        languages: repo.analysis.languages,
        frameworks: repo.analysis.frameworks,
        keyFilesCount: repo.analysis.key_files_count,
        confidenceScore: repo.analysis.confidence_score
      } : null,
      generatedToolsCount: repo.generatedTools?.length || 0,
      hasDockerfile: !!repo.dockerfile
    }));

    return {
      content: [{
        type: 'text',
        text: JSON.stringify(repos, null, 2)
      }]
    };
  }
);

// Get detailed analysis for a repository
mcp.registerTool(
  'get-repository-analysis',
  {
    title: 'Get Repository Analysis',
    description: 'Get detailed analysis results for a stored repository',
    inputSchema: {
      repoId: z.string().describe('Repository ID to get analysis for'),
    },
  },
  async ({ repoId }) => {
    const repo = repositories.get(repoId);
    if (!repo) {
      return {
        content: [{
          type: 'text',
          text: JSON.stringify({
            success: false,
            error: `Repository ${repoId} not found`
          }, null, 2)
        }]
      };
    }

    return {
      content: [{
        type: 'text',
        text: JSON.stringify({
          success: true,
          repoId,
          analysis: repo.analysis,
          keyFiles: repo.keyFiles,
          generatedTools: repo.generatedTools,
          apiEndpoints: repo.apiEndpoints,
          hasDockerfile: !!repo.dockerfile
        }, null, 2)
      }]
    };
  }
);

// Get specific generated MCP tools for a repository
mcp.registerTool(
  'get-generated-tools',
  {
    title: 'Get Generated MCP Tools',
    description: 'Get the AI-generated MCP tools for a specific repository',
    inputSchema: {
      repoId: z.string().describe('Repository ID'),
    },
  },
  async ({ repoId }) => {
    const repo = repositories.get(repoId);
    if (!repo) {
      return {
        content: [{
          type: 'text',
          text: JSON.stringify({
            success: false,
            error: `Repository ${repoId} not found`
          }, null, 2)
        }]
      };
    }

    return {
      content: [{
        type: 'text',
        text: JSON.stringify({
          success: true,
          repoId,
          tools: repo.generatedTools || [],
          toolsCount: repo.generatedTools?.length || 0
        }, null, 2)
      }]
    };
  }
);

// Helper function to analyze file structure
function analyzeFileStructure(files) {
  const structure = {
    languages: new Set(),
    frameworks: new Set(),
    hasDockerfile: false,
    hasPackageJson: false,
    hasCargoToml: false,
    hasPyprojectToml: false,
    directories: new Set(),
  };

  for (const filePath in files) {
    const ext = filePath.split('.').pop()?.toLowerCase();
    const fileName = filePath.split('/').pop();
    const dir = filePath.split('/').slice(0, -1).join('/');
    
    if (dir) structure.directories.add(dir);
    
    // Detect languages
    switch (ext) {
      case 'js':
      case 'ts':
      case 'jsx':
      case 'tsx':
        structure.languages.add('JavaScript/TypeScript');
        break;
      case 'py':
        structure.languages.add('Python');
        break;
      case 'rs':
        structure.languages.add('Rust');
        break;
      case 'go':
        structure.languages.add('Go');
        break;
      case 'java':
        structure.languages.add('Java');
        break;
    }
    
    // Detect frameworks and build files
    if (fileName === 'package.json') structure.hasPackageJson = true;
    if (fileName === 'Cargo.toml') structure.hasCargoToml = true;
    if (fileName === 'pyproject.toml') structure.hasPyprojectToml = true;
    if (fileName === 'Dockerfile') structure.hasDockerfile = true;
    
    // Framework detection based on content
    const content = files[filePath].toLowerCase();
    if (content.includes('react')) structure.frameworks.add('React');
    if (content.includes('next')) structure.frameworks.add('Next.js');
    if (content.includes('express')) structure.frameworks.add('Express');
    if (content.includes('fastapi')) structure.frameworks.add('FastAPI');
    if (content.includes('django')) structure.frameworks.add('Django');
    if (content.includes('tokio')) structure.frameworks.add('Tokio');
  }
  
  return {
    ...structure,
    languages: Array.from(structure.languages),
    frameworks: Array.from(structure.frameworks),
    directories: Array.from(structure.directories),
  };
}

// Helper function to extract API endpoints
function extractApiEndpoints(files) {
  const endpoints = [];
  
  for (const filePath in files) {
    const content = files[filePath];
    
    // Express.js style endpoints
    const expressMatches = content.matchAll(/(?:app|router)\.(get|post|put|delete|patch)\s*\(\s*['"`]([^'"`]+)['"`]/g);
    for (const match of expressMatches) {
      endpoints.push({
        method: match[1].toUpperCase(),
        path: match[2],
        file: filePath,
        framework: 'Express'
      });
    }
    
    // FastAPI style endpoints
    const fastapiMatches = content.matchAll(/@app\.(get|post|put|delete|patch)\s*\(\s*['"`]([^'"`]+)['"`]/g);
    for (const match of fastapiMatches) {
      endpoints.push({
        method: match[1].toUpperCase(),
        path: match[2],
        file: filePath,
        framework: 'FastAPI'
      });
    }
    
    // Next.js API routes (file-based routing)
    if (filePath.includes('/api/') && (filePath.endsWith('.js') || filePath.endsWith('.ts'))) {
      const route = filePath.replace(/.*\/api/, '').replace(/\.(js|ts)$/, '').replace(/\/index$/, '');
      endpoints.push({
        method: 'MULTIPLE',
        path: `/api${route || '/'}`,
        file: filePath,
        framework: 'Next.js'
      });
    }
  }
  
  return endpoints;
}

// Call Intelligent OpenAI Agent for comprehensive analysis and MCP generation  
async function callIntelligentAgent(repoId) {
  const repo = repositories.get(repoId);
  if (!repo) throw new Error(`Repository ${repoId} not found`);
  
  // Prepare streamlined input for Python agent
  const agentInput = {
    repo_id: repoId,
    project_name: repo.projectName,
    description: repo.description,
    tree_structure: repo.treeStructure,
    analysis: repo.analysis,
    important_files: repo.importantFiles.slice(0, 15), // More files for better context
    workspace_path: repo.workspacePath,
    // OpenAI configuration (optional)
    openai_api_key: Deno.env.get('OPENAI_API_KEY'),
    openai_base_url: Deno.env.get('OPENAI_BASE_URL'), // For custom endpoints
    openai_model: Deno.env.get('OPENAI_MODEL') || 'gpt-4o-mini'
  };

  // Call Python LLM agent using uv run
  const command = new Deno.Command("uv", {
    args: ["run", "intelligent_agent.py", "analyze-and-generate"],
    stdin: "piped",
    stdout: "piped", 
    stderr: "piped",
    cwd: "/Users/phytal/Projects/mass/llm"
  });

  const child = command.spawn();
  
  // Send input to Python process
  const writer = child.stdin.getWriter();
  const encoder = new TextEncoder();
  await writer.write(encoder.encode(JSON.stringify(agentInput)));
  await writer.close();

  // Get output from Python process
  const { code, stdout, stderr } = await child.output();
  
  if (code !== 0) {
    const errorText = new TextDecoder().decode(stderr);
    throw new Error(`Python agent failed: ${errorText}`);
  }

  const outputText = new TextDecoder().decode(stdout);
  const result = JSON.parse(outputText);
  
  if (!result.success) {
    throw new Error(`Python agent error: ${result.error}`);
  }

  // Store the results
  repo.generatedTools = result.mcp_tools;
  repo.dockerfile = result.dockerfile;
  repo.aiAnalysis = result.ai_analysis;
  repositories.set(repoId, repo);
  
  return result.mcp_tools;
}

// Generate Dockerfile - handled by Python agent
async function generateDockerfile(repo) {
  // If dockerfile already generated by Python agent, return it
  if (repo.dockerfile) {
    return repo.dockerfile;
  }
  
  // Otherwise trigger Python agent analysis
  await callPythonAgent(repo.id);
  return repo.dockerfile || "# Dockerfile generation failed - please run analyze-repository first";
}

// Deploy repository as container
mcp.registerTool(
  'deploy-repository',
  {
    title: 'Deploy Repository',
    description: 'Build and deploy the stored repository as a container',
    inputSchema: {
      repoId: z.string().describe('Repository ID to deploy'),
      port: z.number().optional().describe('Port to expose (optional)'),
    },
  },
  async ({ repoId, port }) => {
    try {
      const repo = repositories.get(repoId);
      if (!repo) {
        throw new Error(`Repository ${repoId} not found`);
      }

      // Generate Dockerfile if not already generated
      let dockerfile = repo.dockerfile;
      if (!dockerfile) {
        dockerfile = await generateDockerfile(repo);
        repo.dockerfile = dockerfile;
        repositories.set(repoId, repo);
      }

      // Build and deploy
      const buildResult = await orchestrator.buildImage(repoId, dockerfile, repo.files);
      const deployResult = await orchestrator.deployContainer(repoId, buildResult.imageName, { port });

      return {
        content: [{
          type: 'text',
          text: JSON.stringify({
            success: true,
            repoId,
            containerId: deployResult.containerId,
            url: deployResult.url,
            port: deployResult.port,
            status: deployResult.status,
            message: 'Repository deployed successfully'
          }, null, 2)
        }]
      };
    } catch (error) {
      return {
        content: [{
          type: 'text',
          text: JSON.stringify({
            success: false,
            error: error.message,
            repoId
          }, null, 2)
        }]
      };
    }
  }
);

// List deployed containers
mcp.registerTool(
  'list-containers',
  {
    title: 'List Deployed Containers',
    description: 'List all deployed containers and their status',
    inputSchema: {
      repoId: z.string().optional().describe('Filter by repository ID'),
    },
  },
  async ({ repoId }) => {
    const containers = orchestrator.listContainers(repoId);
    
    return {
      content: [{
        type: 'text',
        text: JSON.stringify(containers, null, 2)
      }]
    };
  }
);

// Stop container
mcp.registerTool(
  'stop-container',
  {
    title: 'Stop Container',
    description: 'Stop a deployed container',
    inputSchema: {
      containerId: z.string().describe('Container ID to stop'),
    },
  },
  async ({ containerId }) => {
    try {
      const result = await orchestrator.stopContainer(containerId);
      
      return {
        content: [{
          type: 'text',
          text: JSON.stringify(result, null, 2)
        }]
      };
    } catch (error) {
      return {
        content: [{
          type: 'text',
          text: JSON.stringify({
            success: false,
            error: error.message,
            containerId
          }, null, 2)
        }]
      };
    }
  }
);

// Get container logs
mcp.registerTool(
  'get-container-logs',
  {
    title: 'Get Container Logs',
    description: 'Retrieve logs from a deployed container',
    inputSchema: {
      containerId: z.string().describe('Container ID to get logs from'),
    },
  },
  async ({ containerId }) => {
    try {
      const logs = await orchestrator.getContainerLogs(containerId);
      
      return {
        content: [{
          type: 'text',
          text: logs
        }]
      };
    } catch (error) {
      return {
        content: [{
          type: 'text',
          text: `Error getting logs: ${error.message}`
        }]
      };
    }
  }
);

// Read specific files from the repository
mcp.registerTool(
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
      
      let stat;
      try {
        stat = await Deno.stat(fullPath);
      } catch (error) {
        throw new Error(`File not found: ${filePath}`);
      }
      
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

// List directory contents
mcp.registerTool(
  'list-directory',
  {
    title: 'List Directory Contents',
    description: 'List contents of a directory in the repository',
    inputSchema: {
      dirPath: z.string().optional().describe('Directory path relative to repository root (empty for root)'),
    },
  },
  async ({ dirPath = '' }) => {
    try {
      const fullPath = resolveWithinRoot(WORKSPACE_ROOT, dirPath);
      
      let stat;
      try {
        stat = await Deno.stat(fullPath);
      } catch (error) {
        throw new Error(`Directory not found: ${dirPath || 'root'}`);
      }
      
      if (!stat.isDirectory) {
        throw new Error(`Path is not a directory: ${dirPath || 'root'}`);
      }
      
      const entries = [];
      for await (const entry of Deno.readDir(fullPath)) {
        if (entry.name.startsWith('.') || 
            entry.name === 'node_modules' || 
            entry.name === 'target' ||
            entry.name === '__pycache__') {
          continue;
        }
        
        const entryPath = dirPath ? `${dirPath}/${entry.name}` : entry.name;
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
          type: entry.isDirectory ? 'directory' : 'file',
          size: entryStat.size,
          modified: entryStat.mtime?.toISOString()
        });
      }
      
      entries.sort((a, b) => {
        if (a.type !== b.type) {
          return a.type === 'directory' ? -1 : 1;
        }
        return a.name.localeCompare(b.name);
      });
      
      return {
        content: [{
          type: 'text',
          text: JSON.stringify(entries, null, 2)
        }]
      };
    } catch (error) {
      return {
        content: [{
          type: 'text',
          text: `Error listing directory: ${error.message}`
        }]
      };
    }
  }
);

// Execute terminal commands in the repository
mcp.registerTool(
  'run-command',
  {
    title: 'Run Terminal Command',
    description: 'Execute a terminal command in the repository workspace',
    inputSchema: {
      command: z.string().describe('Command to execute'),
      args: z.array(z.string()).optional().describe('Command arguments'),
    },
  },
  async ({ command, args = [] }) => {
    try {
      const result = await runCommand(command, args);
      
      return {
        content: [{
          type: 'text',
          text: JSON.stringify({
            command: `${command} ${args.join(' ')}`,
            exitCode: result.code,
            output: result.output,
            error: result.error
          }, null, 2)
        }]
      };
    } catch (error) {
      return {
        content: [{
          type: 'text',
          text: `Error executing command: ${error.message}`
        }]
      };
    }
  }
);

// Deploy generated MCP server to a separate port/subdomain
mcp.registerTool(
  'deploy-mcp-server',
  {
    title: 'Deploy Generated MCP Server',
    description: 'Deploy the AI-generated MCP server for a repository as a standalone service',
    inputSchema: {
      repoId: z.string().describe('Repository ID with generated MCP server'),
      subdomain: z.string().optional().describe('Subdomain for the deployed server (auto-generated if not provided)'),
      port: z.number().optional().describe('Port for the deployed server (auto-assigned if not provided)'),
    },
  },
  async ({ repoId, subdomain, port }) => {
    try {
      const repo = repositories.get(repoId);
      if (!repo) {
        throw new Error(`Repository ${repoId} not found`);
      }

      if (!repo.serverTemplate) {
        throw new Error(`No MCP server template generated for repository ${repoId}. Run analyze-repository first.`);
      }

      // Auto-generate subdomain and port if not provided
      const deploySubdomain = subdomain || `${repoId}-mcp`;
      const deployPort = port || (3000 + Math.floor(Math.random() * 1000));

      // Create deployment directory
      const deploymentId = `mcp-${repoId}-${Date.now()}`;
      const deployDir = `/tmp/mcp-deployments/${deploymentId}`;

      // Create deployment files from generated template
      const deployResult = await createMCPDeployment(repo, deployDir, deployPort);

      // Build and deploy container
      const containerResult = await deployMCPContainer(deploymentId, deployDir, deployPort);

      // Store deployment info
      repo.deployment = {
        id: deploymentId,
        subdomain: deploySubdomain,
        port: deployPort,
        url: `http://${deploySubdomain}.localhost:${deployPort}`,
        containerId: containerResult.containerId,
        deployedAt: new Date().toISOString(),
        status: 'running'
      };
      repositories.set(repoId, repo);

      return {
        content: [{
          type: 'text',
          text: JSON.stringify({
            success: true,
            repoId,
            deployment: repo.deployment,
            mcpTools: repo.generatedTools?.length || 0,
            message: `MCP server deployed successfully at ${repo.deployment.url}`
          }, null, 2)
        }]
      };
    } catch (error) {
      return {
        content: [{
          type: 'text',
          text: JSON.stringify({
            success: false,
            error: error.message,
            repoId
          }, null, 2)
        }]
      };
    }
  }
);

// Get generated documentation as MCP resource
mcp.registerTool(
  'get-documentation',
  {
    title: 'Get Generated Documentation',
    description: 'Retrieve the AI-generated documentation for a repository',
    inputSchema: {
      repoId: z.string().describe('Repository ID'),
    },
  },
  async ({ repoId }) => {
    try {
      const repo = repositories.get(repoId);
      if (!repo) {
        throw new Error(`Repository ${repoId} not found`);
      }

      if (!repo.documentation) {
        throw new Error(`No documentation generated for repository ${repoId}. Run analyze-repository first.`);
      }

      return {
        content: [{
          type: 'text',
          text: repo.documentation
        }]
      };
    } catch (error) {
      return {
        content: [{
          type: 'text',
          text: `Error retrieving documentation: ${error.message}`
        }]
      };
    }
  }
);

// List deployed MCP servers
mcp.registerTool(
  'list-deployed-servers',
  {
    title: 'List Deployed MCP Servers',
    description: 'List all deployed MCP servers with their status and URLs',
    inputSchema: {},
  },
  async () => {
    const deployedServers = Array.from(repositories.values())
      .filter(repo => repo.deployment)
      .map(repo => ({
        repoId: repo.id,
        projectName: repo.projectName,
        url: repo.deployment.url,
        status: repo.deployment.status,
        port: repo.deployment.port,
        mcpTools: repo.generatedTools?.length || 0,
        deployedAt: repo.deployment.deployedAt
      }));

    return {
      content: [{
        type: 'text',
        text: JSON.stringify(deployedServers, null, 2)
      }]
    };
  }
);

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

// Create MCP server deployment from generated template
async function createMCPDeployment(repo, deployDir, port) {
  try {
    // Create deployment directory
    await runCommand("mkdir", ["-p", deployDir]);

    // Write all generated server files
    const serverFiles = repo.serverTemplate;
    
    for (const [filename, content] of Object.entries(serverFiles)) {
      const filePath = `${deployDir}/${filename}`;
      await Deno.writeTextFile(filePath, content);
    }

    // Update port in server files if needed
    if (serverFiles['server.ts'] && port !== 3000) {
      let serverContent = serverFiles['server.ts'];
      serverContent = serverContent.replace(/port.*?3000/g, `port: ${port}`);
      await Deno.writeTextFile(`${deployDir}/server.ts`, serverContent);
    }

    return {
      success: true,
      deployDir,
      files: Object.keys(serverFiles)
    };

  } catch (error) {
    throw new Error(`Failed to create MCP deployment: ${error.message}`);
  }
}

// Deploy MCP server container
async function deployMCPContainer(deploymentId, deployDir, port) {
  try {
    const imageName = `mcp-server-${deploymentId}`;
    const containerName = `mcp-container-${deploymentId}`;

    // Build Docker image
    const buildResult = await runCommand("docker", [
      "build", 
      "-t", imageName,
      deployDir
    ]);

    if (buildResult.code !== 0) {
      throw new Error(`Docker build failed: ${buildResult.error}`);
    }

    // Run container
    const runResult = await runCommand("docker", [
      "run",
      "-d",
      "--name", containerName,
      "-p", `${port}:${port}`,
      "--restart", "unless-stopped",
      imageName
    ]);

    if (runResult.code !== 0) {
      throw new Error(`Docker run failed: ${runResult.error}`);
    }

    // Get container ID
    const containerId = runResult.output.trim();

    return {
      success: true,
      containerId,
      imageName,
      containerName,
      port
    };

  } catch (error) {
    throw new Error(`Failed to deploy MCP container: ${error.message}`);
  }
}

// Export setup function for reuse in different transports
export function setupMcpServer(server) {
  // All the MCP resource and tool registrations are already done above
  return server;
}

// HTTP transport handler
MASS.app.all('/socket', async c => {
  const transport = new StreamableHTTPTransport();
  await mcp.connect(transport);

  return transport.handleRequest(c);
});

// Only serve if this is the main module
if (import.meta.main) {
  Deno.serve({ port: MASS.config.port() }, MASS.app.fetch);
}
