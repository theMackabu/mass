# Repository MCP Tools System

This system allows users to store entire repository structures from Cursor IDE and automatically generate MCP tools, Dockerfiles, and deploy containers using an intelligent Python LLM agent.

## Architecture

```
Cursor IDE → Worker (Deno/JS) → Python LLM Agent → OpenAI → Generated MCP Tools
                ↓                       ↓
         [Repository Storage]    [Smart File Analysis]
                ↓                       ↓
         [Container Deployment]  [Context-Aware Generation]
```

## Setup

1. **Install Python dependencies using uv:**
   ```bash
   cd llm/
   uv venv  # Creates .venv automatically
   uv pip install openai pydantic pathspec tiktoken PyYAML python-dotenv aiohttp httpx
   ```

2. **Configure OpenAI (multiple options):**
   
   **Option A: Environment Variables (Recommended)**
   ```bash
   # Copy the example file and edit with your API key
   cp llm/.env.example llm/.env
   # Edit llm/.env with your API key
   ```
   
   **Option B: Manual Export (Groq - Ultra Fast)**
   ```bash
   export OPENAI_API_KEY="your-groq-api-key"
   export OPENAI_BASE_URL="https://api.groq.com/openai/v1"
   export OPENAI_MODEL="openai/gpt-oss-120b"
   # 🚀 10-100x faster than OpenAI, free tier available
   ```
   
   **Option B: Standard OpenAI API**
   ```bash
   export OPENAI_API_KEY="your-openai-api-key"
   # Uses: https://api.openai.com/v1
   ```
   
   **Option B: Custom OpenAI-compatible endpoint**
   ```bash
   export OPENAI_API_KEY="your-api-key"
   export OPENAI_BASE_URL="https://your-custom-endpoint/v1"
   # Examples: Azure OpenAI, Together AI, Anyscale, etc.
   ```
   
   **Option C: Local models (Ollama, vLLM, etc.)**
   ```bash
   export OPENAI_API_KEY="not-needed"
   export OPENAI_BASE_URL="http://localhost:11434/v1"  # Ollama
   export OPENAI_MODEL="llama3.1:8b"  # Custom model name
   ```

3. **Start the MASS server:**
   ```bash
   cargo run
   ```

4. **Connect to the MCP server:**
   - **HTTP/Streamable**: Connect to `/socket` endpoint (for web integrations)  
   - **Stdio**: Use `deno run --allow-read --allow-run mass/worker/stdio.js` (for editors)

5. **Set workspace (optional):**
   ```bash
   export WORKSPACE_ROOT="/path/to/your/project"
   ```

## MCP Resources (Spec-Compliant)

### Repository File System Access  
The server exposes repository files via MCP resources using a properly registered ResourceTemplate:

**Resource Registration:**
```javascript
server.registerResource(
  "repo",
  new ResourceTemplate("repo://{path}", {
    list: { path: "" }, // Advertise repo root for discovery
  }),
  { title: "Repository", description: "Browse workspace files" },
  async (uri, { path }) => { /* handler */ }
);
```

**Discovery Flow:**
1. **resources/list** → Client discovers `repo://{path}` template
2. **resources/read** → Client constructs URIs and reads content

**Benefits:**
- **Standards-compliant**: Uses official ResourceTemplate API
- **Efficient**: Host fetches only needed files on-demand  
- **Secure**: Path traversal protection and workspace scoping
- **Discoverable**: Template advertised via resources/list
- **Scalable**: Works with repositories of any size

**Example Usage:**
```javascript
// Client discovers template via resources/list first
const templates = await mcp.listResources();

// Read repository root (empty path)
const rootListing = await mcp.readResource('repo://');

// Read specific files  
const packageJson = await mcp.readResource('repo://package.json');
const srcApp = await mcp.readResource('repo://src/App.js');

// Browse subdirectories
const srcListing = await mcp.readResource('repo://src');
```

**Content Types:**
- **Directories**: JSON listings with `application/json` MIME type
- **Text files**: Plain text with `text/plain` MIME type  
- **Binary files**: Base64 blob with `application/octet-stream` MIME type

## Streamlined MCP Workflow: Two Core Tools

### 🚀 **Tool 1: `generate-mcp-server`**

The user calls this single tool to analyze their repository and build the complete MCP server:

```javascript
await mcp.callTool('generate-mcp-server', {
  repoId: 'my-awesome-project',
  projectName: 'My Awesome Project',
  description: 'A React frontend with Express.js backend',
  maxFiles: 20  // Optional: limit important files analyzed
});
```

**What happens behind the scenes:**
1. Creates `tar.gz` archive of the repository
2. Extracts and analyzes using Rust operations
3. Detects languages, frameworks, config files
4. Identifies important files (package.json, main.js, etc.)
5. Calls Python LLM agent for intelligent analysis
6. Generates contextual MCP tools based on detected patterns
7. Creates complete documentation
8. Builds deployable MCP server files

**Complete Response:**
```json
{
  "success": true,
  "repoId": "my-awesome-project",
  "analysis": {
    "file_count": 45,
    "languages": ["JavaScript", "TypeScript"],
    "config_files": ["package.json", "Dockerfile"],
    "size_bytes": 1024000,
    "frameworks": ["React", "Express.js", "MongoDB"]
  },
  "generatedTools": [
    {
      "name": "test-api-endpoint",
      "title": "Test API Endpoint",
      "description": "Test REST API endpoints with proper payloads",
      "input_schema": {
        "endpoint": "string",
        "method": "string",
        "payload": "object"
      },
      "category": "api",
      "usage": "await mcp.callTool('test-api-endpoint', {endpoint: '/api/users', method: 'GET'})"
    },
    {
      "name": "build-react-app",
      "title": "Build React Application",
      "description": "Build React app with environment selection",
      "input_schema": {
        "environment": "string"
      },
      "category": "development",
      "usage": "await mcp.callTool('build-react-app', {environment: 'production'})"
    },
    {
      "name": "query-mongodb",
      "title": "Query MongoDB Database",
      "description": "Execute MongoDB queries on detected models",
      "input_schema": {
        "collection": "string",
        "query": "object"
      },
      "category": "database",
      "usage": "await mcp.callTool('query-mongodb', {collection: 'users', query: {status: 'active'}})"
    },
    {
      "name": "run-test-suite",
      "title": "Run Test Suite",
      "description": "Execute Jest/Mocha tests with coverage",
      "input_schema": {
        "testPattern": "string"
      },
      "category": "development",
      "usage": "await mcp.callTool('run-test-suite', {testPattern: 'api/**/*.test.js'})"
    },
    {
      "name": "deploy-to-staging",
      "title": "Deploy to Staging",
      "description": "Deploy to staging environment",
      "input_schema": {
        "environment": "string"
      },
      "category": "deployment",
      "usage": "await mcp.callTool('deploy-to-staging', {environment: 'staging'})"
    },
    {
      "name": "analyze-bundle-size",
      "title": "Analyze Bundle Size",
      "description": "Analyze webpack bundle with recommendations",
      "input_schema": {},
      "category": "analysis",
      "usage": "await mcp.callTool('analyze-bundle-size', {})"
    }
  ],
  "documentation": {
    "overview": "React + Express.js fullstack application with MongoDB integration...",
    "architecture": "Frontend: React SPA, Backend: Express.js REST API, Database: MongoDB...",
    "apiEndpoints": [
      {
        "path": "/api/users",
        "method": "GET",
        "description": "Retrieve user list with pagination",
        "parameters": ["page", "limit"],
        "response": "Array of user objects"
      },
      {
        "path": "/api/auth/login",
        "method": "POST",
        "description": "Authenticate user with email/password",
        "parameters": ["email", "password"],
        "response": "JWT token and user data"
      }
    ],
    "keyFunctions": [
      {
        "name": "authenticateUser",
        "file": "src/auth/middleware.js:15",
        "description": "JWT token validation middleware"
      },
      {
        "name": "processPayment",
        "file": "src/payment/stripe.js:42",
        "description": "Stripe payment processing logic"
      }
    ],
    "developmentGuide": "To run locally: npm install && npm run dev...",
    "deploymentGuide": "Deploy with Docker: docker build -t app . && docker run -p 3000:3000 app..."
  },
  "serverGenerated": true,
  "toolsCount": 6,
  "message": "Generated complete MCP server with 6 tools and comprehensive documentation. Ready for deployment."
}
```

### 🚀 **Tool 2: `deploy-mcp-server`**

The user then calls this tool to deploy the generated MCP server:

```javascript
await mcp.callTool('deploy-mcp-server', {
  repoId: 'my-awesome-project',
  subdomain: 'my-project-mcp',  // Optional: auto-generated if not provided
  port: 3001                    // Optional: auto-assigned if not provided
});
```

**What happens:**
1. Takes the generated MCP server files from Tool 1
2. Creates deployment directory with all necessary files
3. Builds Docker container with the MCP server
4. Deploys container with auto-assigned port
5. Returns connection instructions

**Deployment Response:**
```json
{
  "success": true,
  "repoId": "my-awesome-project",
  "deployment": {
    "id": "mcp-my-awesome-project-1703123456789",
    "subdomain": "my-project-mcp",
    "port": 3001,
    "url": "http://my-project-mcp.localhost:3001",
    "containerId": "mcp-container-my-awesome-project-1703123456789",
    "deployedAt": "2023-12-21T10:30:56.789Z",
    "status": "running"
  },
  "connectionInstructions": {
    "httpConnection": {
      "url": "http://my-project-mcp.localhost:3001",
      "description": "Connect via HTTP for web integrations"
    },
    "stdioConnection": {
      "command": "deno run --allow-net http://my-project-mcp.localhost:3001/stdio",
      "description": "Connect via stdio for editors like Cursor"
    },
    "dockerConnection": {
      "command": "docker run -p 3001:3001 mcp-my-awesome-project",
      "description": "Run locally with Docker"
    }
  },
  "availableTools": [
    "test-api-endpoint",
    "build-react-app",
    "query-mongodb",
    "run-test-suite",
    "deploy-to-staging",
    "analyze-bundle-size"
  ],
  "usageExample": {
    "connect": "const mcp = new McpClient('http://my-project-mcp.localhost:3001')",
    "callTool": "await mcp.callTool('test-api-endpoint', {endpoint: '/api/users', method: 'GET'})"
  },
  "message": "MCP server deployed successfully! Connect using the instructions above."
}
```

### 📋 **Complete Workflow**

1. **Generate**: `generate-mcp-server` → Analyzes repo, creates tools & documentation
2. **Deploy**: `deploy-mcp-server` → Deploys as standalone MCP server
3. **Connect**: User connects to their custom MCP server and uses generated tools

## Legacy Tools (Still Available)

### Repository Management

#### get-repo-tree
Get the file tree structure using the `tree` command.

#### store-repository
Stores externally provided repository structure (for Cursor IDE integration).

#### list-repositories
Lists all stored repositories with enhanced analysis metadata.

#### get-repository-analysis
Get detailed analysis results for a specific repository.

#### get-generated-tools
Get the AI-generated MCP tools for a specific repository.

### Terminal & System Operations

#### 5. run-command
Execute terminal commands in the repository workspace.

**Parameters:**
- `command` (string): Command to execute (e.g., "npm", "cargo", "python")
- `args` (array, optional): Command arguments

**Examples:**
- `run-command("npm", ["run", "build"])` - Build project  
- `run-command("tree", ["-L", "2"])` - Show directory structure
- `run-command("git", ["status"])` - Check git status

#### 6. read-file / list-directory (via MCP Resources)
Access files through the `repo://` resource system (see MCP Resources section).

### Container Management

#### 7. generate-dockerfile
Generates a production-ready Dockerfile using AI analysis.

**Parameters:**
- `repoId` (string): Repository ID

#### 8. deploy-repository
Builds and deploys the repository as a container.

**Parameters:**
- `repoId` (string): Repository ID to deploy
- `port` (number, optional): Port to expose

#### 9. list-containers
Lists all deployed containers.

**Parameters:**
- `repoId` (string, optional): Filter by repository ID

#### 10. stop-container
Stops a deployed container.

**Parameters:**
- `containerId` (string): Container ID to stop

#### 11. get-container-logs
Retrieves logs from a deployed container.

**Parameters:**
- `containerId` (string): Container ID

## Intelligent Analysis Workflow

### Phase 1: Streamlined Repository Processing

**Terminal Commands + Rust Analysis (New Approach)**
1. **Tree Structure**: `tree` command generates clean directory visualization
2. **Archive Creation**: `tar -czf` creates compressed repository archive
3. **Rust Processing**: Fast extraction and analysis using native operations
4. **Smart File Selection**: Rust identifies important files by patterns
5. **Structured Data**: LLM receives organized analysis instead of raw files

**Benefits vs File Traversal:**
- 🚀 **10x Faster**: No JavaScript file system operations
- 📦 **Compressed Transfer**: Efficient tar.gz handling  
- 🦀 **Native Performance**: Rust operations for heavy lifting
- 🧠 **Better AI Context**: Structured data vs raw file dumps
- 🛡️ **More Reliable**: Standard Unix tools + Rust safety

### Phase 2: Intelligent Analysis
4. **Project Type Detection**: Identifies project as:
   - Web Frontend (React, Vue, Angular)
   - Web Backend (Express, FastAPI, Django)
   - Fullstack application
   - CLI tool, Library, Microservice, etc.

5. **Framework & Language Detection**: 
   - Analyzes import statements and dependencies
   - Detects frameworks from code patterns
   - Maps file extensions to languages

6. **API Endpoint Extraction**:
   - Parses Express.js routes (`app.get('/api/users')`)
   - Detects FastAPI endpoints (`@app.get('/users')`)
   - Identifies Django URL patterns
   - Next.js file-based routing

### Phase 3: AI-Powered Generation
7. **Context Building**: Creates rich context for OpenAI:
   - Project metadata and file structure
   - Key file contents (first 500 chars each)
   - Detected patterns and frameworks
   - API endpoints and database info

8. **MCP Tool Generation**: OpenAI generates 4-6 contextual tools:
   - **API Testing Tools**: Test detected endpoints
   - **Build Tools**: Framework-specific build commands  
   - **Database Tools**: Query/migration tools for detected DBs
   - **Deployment Tools**: Environment-specific deployment
   - **Analysis Tools**: Bundle analysis, dependency checks

9. **Dockerfile Generation**: AI creates production-ready Dockerfile:
   - Appropriate base images for detected stack
   - Multi-stage builds for frontend projects
   - Optimized layer caching
   - Security best practices

### Phase 4: Deployment & Management
10. **Container Orchestration**: Deploy generated containers
11. **Monitoring**: Real-time logs and health checks
12. **Tool Usage**: Generated MCP tools available for development

## Supported Languages & Frameworks

### Languages
- JavaScript/TypeScript
- Python
- Rust
- Go
- Java

### Frameworks
- React/Next.js
- Express.js
- FastAPI
- Django
- Tokio

## AI-Generated Tools Examples

The Python LLM agent generates 4-6 highly contextual MCP tools based on intelligent codebase analysis:

### For React + Express Fullstack Apps:
- **`test-api-endpoint`** - Test `/api/users`, `/api/auth` endpoints with proper payloads
- **`build-react-app`** - Run `npm run build` with environment selection  
- **`query-mongodb`** - Execute MongoDB queries on detected User, Product models
- **`run-test-suite`** - Execute Jest/Mocha tests with coverage reporting
- **`deploy-to-aws`** - Deploy to AWS with detected env vars and configs
- **`analyze-bundle-size`** - Analyze webpack bundle with recommendations

### For FastAPI + Python Projects:
- **`test-fastapi-endpoints`** - Test OpenAPI documented endpoints
- **`run-database-migration`** - Execute Alembic migrations
- **`generate-api-docs`** - Update FastAPI OpenAPI documentation
- **`run-pytest-suite`** - Execute pytest with coverage and fixtures
- **`deploy-to-docker`** - Build and deploy Docker container
- **`check-dependencies`** - Analyze pip dependencies for security issues

### For Rust CLI Projects:
- **`cargo-build-release`** - Build optimized release binary
- **`run-cargo-tests`** - Execute test suite with output formatting
- **`check-clippy-lints`** - Run Clippy linter with recommendations  
- **`benchmark-performance`** - Run criterion benchmarks
- **`cross-compile-targets`** - Build for multiple architectures
- **`generate-docs`** - Generate and serve rustdoc documentation

### For Next.js Projects:
- **`test-api-routes`** - Test `/api/*` routes with proper Next.js context
- **`build-for-production`** - Run Next.js build with optimization analysis
- **`analyze-page-performance`** - Test Core Web Vitals for pages
- **`deploy-to-vercel`** - Deploy with Vercel CLI and environment configs
- **`run-lighthouse-audit`** - Performance, accessibility, and SEO audit
- **`manage-database-schema`** - Prisma schema management and migrations

## Clean Architecture

```
┌─────────────┐    ┌──────────────┐    ┌─────────────────┐    ┌─────────────┐
│ Cursor IDE  │───▶│ MASS Server  │───▶│ Rust Ops       │───▶│ Python LLM  │
│   (MCP)     │    │  (Deno/JS)   │    │ (Native Speed)  │    │ Agent       │
└─────────────┘    └──────────────┘    └─────────────────┘    └─────────────┘
                           │                       │                     │
                           ▼                       ▼                     ▼
                   ┌──────────────┐    ┌─────────────────┐    ┌─────────────────┐
                   │ MCP Tools    │    │ tar.gz Archive  │    │ Generated MCP   │
                   │ Registration │    │ Extraction &    │    │ Tools & Docker  │
                   └──────────────┘    │ Analysis        │    └─────────────────┘
                           │           └─────────────────┘              │
                           ▼                       │                    ▼
                   ┌──────────────┐              ▼          ┌─────────────────┐
                   │ Terminal     │    ┌─────────────────┐  │ Container       │
                   │ Commands     │    │ Structured Data │  │ Deployment      │
                   │ (tree, tar)  │    │ for LLM         │  │                 │
                   └──────────────┘    └─────────────────┘  └─────────────────┘
```

### Key Components:

1. **MASS Server (Deno/JS)**: Pure MCP tool registration, no LLM calls
2. **Terminal Commands**: `tree` for structure, `tar` for archiving
3. **Rust Operations**: Fast extraction, analysis, file selection
4. **Python LLM Agent**: Handles all AI/OpenAI interactions
5. **Container Orchestrator**: Docker container management

### Separation of Concerns:
- **Deno/JS**: MCP protocol orchestration, terminal commands, Rust ops, container deployment
- **Rust**: Heavy lifting (tar extraction, file analysis, language detection)  
- **Python + OpenAI**: Intelligent codebase analysis, API endpoint detection, MCP tool generation
- **Docker**: Isolated deployment of generated MCP servers

### AI-Powered Intelligence:
- **Flexible AI Backend**: Supports OpenAI API, custom endpoints, or local models
- **Smart Analysis**: Identifies API endpoints, business logic, and integrations
- **Context-aware generation**: Creates MCP tools specific to detected functionality
- **Comprehensive documentation**: Auto-generated developer guides and API references
- **Deployable servers**: Complete MCP server implementations ready for container deployment

### Supported AI Providers:
- **OpenAI**: GPT-4o-mini, GPT-4, GPT-3.5-turbo
- **Azure OpenAI**: Enterprise OpenAI models
- **Together AI**: Open source models (Llama, Mistral, etc.)
- **Anyscale**: Ray-based model serving
- **Local Models**: Ollama, vLLM, LocalAI, LM Studio
- **Any OpenAI-compatible API**: Just set OPENAI_BASE_URL

### Python Environment:
- **uv**: Fast Python package manager and runner (`uv pip install openai`)
- **uv run**: Executes agent.py.py with proper environment
- **.venv**: Auto-managed virtual environment with OpenAI SDK

## File Structure Analysis

The system analyzes:
- Programming languages used
- Frameworks and libraries
- API endpoints and routes
- Build configuration files
- Directory structure
- Dependencies

This analysis drives intelligent tool generation and Dockerfile creation.

## Example Integration

```javascript
// In Cursor IDE MCP client
const result = await mcp.callTool('store-repository', {
  repoId: 'my-project-123',
  projectName: 'My Awesome Project',
  files: await getAllProjectFiles(), // Your implementation
});

console.log(`Generated ${result.generatedTools} tools`);

// Deploy the project
const deployment = await mcp.callTool('deploy-repository', {
  repoId: 'my-project-123'
});

console.log(`Deployed at: ${deployment.url}`);
```

## Security Notes

- Repository files are stored in memory (consider adding persistent storage)
- OpenAI API calls include code snippets (ensure compliance with your policies)
- Container deployment is simulated (integrate with actual Docker API for production)
- No authentication implemented (add as needed)

## Next Steps

1. Integrate with real Docker API
2. Add persistent storage for repositories
3. Implement user authentication
4. Add container health monitoring
5. Support for more languages and frameworks