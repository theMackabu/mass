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
   
   **Option A: Standard OpenAI API**
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

## Available MCP Tools

### Streamlined Repository Analysis

#### 1. get-repo-tree
Get the file tree structure using the `tree` command.

**Parameters:** None

**What it does:**
- Executes `tree -a -I "node_modules|target|.git" -L 4` command
- Returns clean directory structure visualization
- Skips common build/dependency directories
- Falls back to `find` if tree command unavailable

#### 2. analyze-repository ⭐ **RECOMMENDED**
Complete repository analysis using tar.gz archive and Rust processing.

**Parameters:**
- `repoId` (string): Unique identifier for the repository
- `projectName` (string, optional): Project name  
- `description` (string, optional): Project description
- `maxFiles` (number, optional): Maximum important files to extract (default: 20)

**What it does:**
1. **Creates tar.gz archive** using `tar -czf` with smart exclusions
2. **Extracts to temp directory** using Rust tar/gzip operations
3. **Analyzes with Rust**: File count, languages, config files, size
4. **Extracts important files**: Configuration, entry points, README
5. **Generates MCP tools** using Python LLM agent with structured data
6. **Cleans up** temporary files automatically

**Advantages:**
- ⚡ **Fast**: No recursive file traversal in JavaScript
- 🗜️ **Efficient**: Compressed archive transfer
- 🦀 **Reliable**: Rust-powered analysis operations
- 🧠 **Smart**: LLM receives structured data, not raw files

#### 2. store-repository
Stores externally provided repository structure (for Cursor IDE integration).

**Parameters:**
- `repoId` (string): Unique identifier for the repository
- `files` (object): Mapping of file paths to their content
- `projectName` (string, optional): Project name  
- `description` (string, optional): Project description

**Example:**
```json
{
  "repoId": "my-fullstack-app", 
  "projectName": "My Fullstack Application",
  "description": "React frontend with Express.js backend",
  "files": {
    "package.json": "{ \"name\": \"my-app\", \"dependencies\": {...} }",
    "server.js": "const express = require('express'); app.get('/api/users'...)",
    "client/src/App.js": "import React from 'react'; function App() {...}"
  }
}
```

#### 2. list-repositories
Lists all stored repositories with enhanced analysis metadata.

**Response includes:**
- Basic repo info (name, description, file count)
- Analysis results (project type, languages, frameworks)
- Generated tools count and Dockerfile status
- Confidence scores and key file analysis

#### 3. get-repository-analysis
Get detailed analysis results for a specific repository.

**Parameters:**
- `repoId` (string): Repository ID

**Returns:**
- Full project analysis (type, languages, frameworks)
- Key files selected for analysis with importance scores
- Generated MCP tools with implementation hints
- API endpoints detected
- Dockerfile generation status

#### 4. get-generated-tools
Get the AI-generated MCP tools for a specific repository.

**Parameters:**
- `repoId` (string): Repository ID

**Returns contextual tools like:**
- `test-api-endpoint` - Test REST API endpoints
- `build-frontend` - Build React/Vue/Angular projects  
- `run-database-migration` - Execute database migrations
- `analyze-bundle-size` - Analyze webpack bundle
- `deploy-to-staging` - Deploy to staging environment

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
- **uv run**: Executes intelligent_agent.py with proper environment
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