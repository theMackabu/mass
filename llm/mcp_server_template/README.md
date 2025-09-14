# MCP Server Template

This template provides a simple MCP server that can work with any cloned GitHub repository.

## Setup

1. **Copy the template files** to your cloned repository:
   ```bash
   cp mcp_server_template/* /path/to/cloned/repo/
   cd /path/to/cloned/repo/
   ```

2. **Install dependencies**:
   ```bash
   npm install
   ```

3. **Generate MCP tools** (if not already done):
   ```bash
   # Run the LLM analysis to generate mcp_tools.json and documentation.md
   python3 /path/to/llm/agent.py analyze-and-generate < input.json > output.json
   ```

4. **Start the server**:
   ```bash
   npm start
   ```

## Features

- **MCP Protocol**: Full MCP server implementation
- **HTTP API**: Web-accessible endpoints for tools and documentation
- **Dynamic Loading**: Automatically loads generated MCP tools from `mcp_tools.json`
- **Documentation**: Serves generated documentation at `/docs`
- **Health Check**: Available at `/health`

## API Endpoints

- `GET /health` - Server health status
- `GET /tools` - List all available MCP tools
- `GET /docs` - Get generated documentation
- `POST /tools/:name` - Execute a specific tool

## MCP Tools

The server automatically loads MCP tools from `mcp_tools.json` if present. If not found, it provides default tools for repository analysis.

## Docker Support

Use the generated Dockerfile to containerize the MCP server:

```bash
docker build -t mcp-server .
docker run -p 3000:3000 mcp-server
```

## Integration

This server can be integrated with:
- Claude Desktop (via MCP protocol)
- Web applications (via HTTP API)
- CI/CD pipelines (via HTTP API)
- Development tools (via MCP protocol)
