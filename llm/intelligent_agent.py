#!/usr/bin/env python3
"""
OpenAI-Powered Intelligent MCP Agent

This agent uses OpenAI GPT-4 to:
1. Analyze codebases intelligently 
2. Identify relevant API endpoints and methods
3. Generate contextual MCP tools
4. Create comprehensive documentation
5. Build deployable MCP server templates
"""

import asyncio
import json
import sys
import os
import re
from typing import Dict, Any, Optional, List
from pathlib import Path

try:
    import openai
    from openai import AsyncOpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    print("Warning: OpenAI not available. Install with: uv pip install openai", file=sys.stderr)

class IntelligentMCPAgent:
    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None):
        self.api_key = api_key or os.getenv('OPENAI_API_KEY')
        self.base_url = base_url or os.getenv('OPENAI_BASE_URL')  # Allow custom base URL
        
        if not self.api_key:
            raise ValueError("OpenAI API key required. Set OPENAI_API_KEY environment variable.")
        
        # Initialize client with optional base_url
        client_kwargs = {"api_key": self.api_key}
        if self.base_url:
            client_kwargs["base_url"] = self.base_url
            print(f"Using custom OpenAI base URL: {self.base_url}", file=sys.stderr)
        
        self.client = AsyncOpenAI(**client_kwargs)
        
        # Model selection - can be overridden via environment variable
        self.model = os.getenv('OPENAI_MODEL', 'gpt-4o-mini')  # Fast and cost-effective for code analysis
        print(f"Using model: {self.model}", file=sys.stderr)

    async def analyze_codebase_context(self, tree_structure: str, analysis: Dict[str, Any], 
                                     important_files: List[str]) -> Dict[str, Any]:
        """
        Use OpenAI to intelligently analyze the codebase and identify key patterns
        """
        
        # Prepare context for the LLM
        context = self._build_analysis_context(tree_structure, analysis, important_files)
        
        prompt = f"""
Analyze this codebase and identify:

1. **API Endpoints & Methods**: List all exposed API endpoints, functions, or methods that could be called externally
2. **Key Business Logic**: Important functions, classes, or modules that represent core functionality  
3. **Database/Storage Operations**: Any data persistence, queries, or storage operations
4. **External Integrations**: Third-party APIs, services, or external system connections
5. **Configuration & Environment**: Important config files, environment variables, or settings

Context:
{context}

Return a JSON object with this structure:
{{
  "api_endpoints": [
    {{
      "method": "GET|POST|PUT|DELETE", 
      "path": "/api/endpoint", 
      "function": "functionName",
      "description": "What this endpoint does",
      "parameters": ["param1", "param2"],
      "file": "path/to/file.js"
    }}
  ],
  "key_functions": [
    {{
      "name": "functionName",
      "description": "What this function does", 
      "file": "path/to/file.js",
      "type": "business_logic|data_operation|integration|utility"
    }}
  ],
  "database_operations": [
    {{
      "operation": "create|read|update|delete|query",
      "entity": "User|Product|Order",
      "description": "What this operation does",
      "file": "path/to/file.js"
    }}
  ],
  "external_integrations": [
    {{
      "service": "ServiceName",
      "type": "api|database|queue|storage", 
      "description": "Integration purpose",
      "file": "path/to/file.js"
    }}
  ],
  "project_summary": "Brief overview of what this codebase does",
  "architecture_pattern": "REST API|GraphQL|Microservice|CLI|Library|WebApp",
  "main_technologies": ["React", "Express", "MongoDB", "etc"]
}}
"""

        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an expert software architect analyzing codebases. Return valid JSON only."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3
            )
            
            result = json.loads(response.choices[0].message.content)
            return result
            
        except Exception as e:
            print(f"Error in OpenAI analysis: {e}", file=sys.stderr)
            return self._fallback_analysis(tree_structure, analysis, important_files)

    async def generate_mcp_tools(self, codebase_analysis: Dict[str, Any], 
                               repo_metadata: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Generate MCP tools based on the intelligent codebase analysis
        """
        
        prompt = f"""
Based on this codebase analysis, generate 5-8 highly useful MCP tools that would help developers work with this specific project.

Codebase Analysis:
{json.dumps(codebase_analysis, indent=2)}

Repository Info:
- Name: {repo_metadata.get('project_name', 'Unknown')}  
- Type: {codebase_analysis.get('architecture_pattern', 'Unknown')}
- Technologies: {', '.join(codebase_analysis.get('main_technologies', []))}

For each MCP tool, create:
1. **API Testing Tools** - For each detected API endpoint
2. **Business Logic Tools** - For key functions and operations  
3. **Database Tools** - For data operations (if any)
4. **Integration Tools** - For external service interactions
5. **Development Tools** - Build, test, deploy, monitor

Return JSON array with this structure:
[
  {{
    "name": "kebab-case-name",
    "title": "Human Readable Title",
    "description": "Detailed description of what this tool does",
    "input_schema": {{
      "param1": "string",
      "param2": "number", 
      "optional_param": "boolean"
    }},
    "category": "api|business_logic|database|integration|development",
    "implementation": {{
      "type": "http_request|function_call|command|query",
      "endpoint": "/api/endpoint",
      "method": "GET|POST|PUT|DELETE",
      "function": "functionName", 
      "file": "path/to/file.js",
      "example_usage": "Example of how to use this tool"
    }},
    "purpose": "Why this tool is useful for this specific codebase"
  }}
]

Focus on tools that would actually be useful for developers working with this project. Make them specific to the detected functionality.
"""

        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an expert at creating practical developer tools. Generate tools that developers would actually want to use. Return valid JSON array only."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7
            )
            
            tools = json.loads(response.choices[0].message.content)
            return tools
            
        except Exception as e:
            print(f"Error generating MCP tools: {e}", file=sys.stderr)
            return self._fallback_tools(codebase_analysis)

    async def generate_documentation_resource(self, codebase_analysis: Dict[str, Any], 
                                            mcp_tools: List[Dict[str, Any]],
                                            repo_metadata: Dict[str, Any]) -> str:
        """
        Generate comprehensive documentation as an MCP resource
        """
        
        prompt = f"""
Create comprehensive developer documentation for this codebase and its generated MCP tools.

Codebase Analysis:
{json.dumps(codebase_analysis, indent=2)}

Generated MCP Tools:
{json.dumps(mcp_tools, indent=2)}

Repository: {repo_metadata.get('project_name', 'Project')}

Create documentation with these sections:

# {repo_metadata.get('project_name', 'Project')} - Developer Guide

## Project Overview
- What this project does
- Architecture pattern and key technologies
- Main components and structure

## API Reference  
- List all detected endpoints with descriptions
- Parameters, responses, and examples
- Authentication/authorization if detected

## Key Functions & Business Logic
- Important functions and their purposes
- Data models and relationships  
- Business rules and workflows

## Available MCP Tools
- Each tool with description and usage examples
- Categories: API Testing, Business Logic, Database, etc.
- Integration examples for common workflows

## Development Guide
- How to set up and run the project
- Testing strategies and available tools
- Deployment and monitoring approaches

## External Integrations
- Third-party services and APIs used
- Configuration requirements
- Security considerations

Make this practical and useful for developers who need to understand and work with this codebase.
Use clear markdown formatting with code examples where helpful.
"""

        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a technical writer creating developer documentation. Write clear, comprehensive documentation that helps developers understand and use the codebase effectively."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.4
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            print(f"Error generating documentation: {e}", file=sys.stderr)
            return self._fallback_documentation(codebase_analysis, mcp_tools, repo_metadata)

    async def generate_mcp_server_template(self, mcp_tools: List[Dict[str, Any]], 
                                         documentation: str,
                                         repo_metadata: Dict[str, Any]) -> Dict[str, str]:
        """
        Generate a complete MCP server implementation that can be deployed
        """
        
        prompt = f"""
Generate a complete, deployable MCP server implementation with these components:

1. **package.json** - Node.js project with MCP SDK dependencies
2. **server.js** - MCP server implementing all the tools
3. **Dockerfile** - Container for deployment  
4. **README.md** - Deployment and usage instructions

MCP Tools to implement:
{json.dumps(mcp_tools, indent=2)}

Repository context: {repo_metadata.get('project_name', 'Project')}

Requirements:
- Use @modelcontextprotocol/sdk for MCP server
- Implement all tools with proper error handling
- Include the documentation as an MCP resource  
- Use TypeScript for better type safety
- Include health check endpoints
- Production-ready with proper logging

Return JSON with file contents:
{{
  "package.json": "...",
  "server.ts": "...", 
  "Dockerfile": "...",
  "README.md": "...",
  "tsconfig.json": "..."
}}
"""

        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an expert Node.js developer creating production-ready MCP servers. Generate complete, working code with proper error handling and TypeScript types."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3
            )
            
            server_files = json.loads(response.choices[0].message.content)
            
            # Add the documentation as a separate file
            server_files["documentation.md"] = documentation
            
            return server_files
            
        except Exception as e:
            print(f"Error generating MCP server: {e}", file=sys.stderr)
            return self._fallback_server_template(mcp_tools, documentation, repo_metadata)

    def _build_analysis_context(self, tree_structure: str, analysis: Dict[str, Any], 
                               important_files: List[str]) -> str:
        """Build context for OpenAI analysis"""
        
        context = f"""
PROJECT STRUCTURE:
{tree_structure}

BASIC ANALYSIS:
- Languages: {', '.join(analysis.get('languages', []))}
- Config Files: {', '.join(analysis.get('config_files', []))}  
- File Count: {analysis.get('file_count', 0)}
- Size: {analysis.get('size_bytes', 0)} bytes

KEY FILES (first 10):
"""
        
        # Add important file contents (truncated)
        for i, file_content in enumerate(important_files[:10]):
            if ':' in file_content:
                filename, content = file_content.split(':', 1)
                # Truncate very long files
                if len(content) > 2000:
                    content = content[:2000] + "\n... [truncated]"
                context += f"\n--- {filename} ---\n{content}\n"
        
        return context

    def _fallback_analysis(self, tree_structure: str, analysis: Dict[str, Any], 
                          important_files: List[str]) -> Dict[str, Any]:
        """Fallback analysis when OpenAI fails"""
        return {
            "api_endpoints": [],
            "key_functions": [],
            "database_operations": [],
            "external_integrations": [],
            "project_summary": f"Project with {analysis.get('file_count', 0)} files using {', '.join(analysis.get('languages', []))}",
            "architecture_pattern": "Unknown",
            "main_technologies": analysis.get('languages', [])
        }

    def _fallback_tools(self, codebase_analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate basic fallback tools"""
        return [
            {
                "name": "analyze-project",
                "title": "Analyze Project",
                "description": "Basic project analysis and overview",
                "input_schema": {},
                "category": "development",
                "implementation": {
                    "type": "command",
                    "example_usage": "Get basic project information"
                },
                "purpose": "Fallback tool when OpenAI analysis fails"
            }
        ]

    def _fallback_documentation(self, codebase_analysis: Dict[str, Any], 
                               mcp_tools: List[Dict[str, Any]], 
                               repo_metadata: Dict[str, Any]) -> str:
        """Generate basic fallback documentation"""
        return f"""# {repo_metadata.get('project_name', 'Project')} Documentation

## Overview
{codebase_analysis.get('project_summary', 'No summary available')}

## Technologies
{', '.join(codebase_analysis.get('main_technologies', []))}

## Available MCP Tools
{len(mcp_tools)} tools generated for this project.

## Status
Documentation generated with fallback method - OpenAI analysis failed.
"""

    def _fallback_server_template(self, mcp_tools: List[Dict[str, Any]], 
                                 documentation: str, 
                                 repo_metadata: Dict[str, Any]) -> Dict[str, str]:
        """Generate basic fallback server template"""
        return {
            "package.json": json.dumps({
                "name": f"mcp-server-{repo_metadata.get('project_name', 'project')}",
                "version": "1.0.0",
                "type": "module",
                "dependencies": {
                    "@modelcontextprotocol/sdk": "^0.5.0"
                }
            }, indent=2),
            "server.ts": f"""// Basic MCP server template
import {{ McpServer }} from '@modelcontextprotocol/sdk/server/mcp';

const server = new McpServer({{
  name: '{repo_metadata.get('project_name', 'project')}',
  version: '1.0.0'
}});

// Add your tools here
console.log('MCP server starting...');
""",
            "README.md": f"# {repo_metadata.get('project_name', 'Project')} MCP Server\n\nGenerated MCP server with {len(mcp_tools)} tools."
        }

# CLI Interface
async def main():
    if len(sys.argv) < 2:
        print(json.dumps({
            "error": "Usage: uv run intelligent_agent.py <command>",
            "commands": ["analyze-and-generate", "health-check"]
        }))
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == "health-check":
        if OPENAI_AVAILABLE:
            print(json.dumps({
                "success": True,
                "service": "intelligent-mcp-agent",
                "openai_available": True,
                "status": "healthy"
            }))
        else:
            print(json.dumps({
                "success": False,
                "service": "intelligent-mcp-agent", 
                "openai_available": False,
                "error": "OpenAI not available"
            }))
        return
    
    if command == "analyze-and-generate":
        if not OPENAI_AVAILABLE:
            print(json.dumps({
                "success": False,
                "error": "OpenAI library not available. Install with: uv pip install openai"
            }))
            sys.exit(1)
        
        try:
            # Read input from stdin
            input_data = json.loads(sys.stdin.read())
            
            # Allow custom base URL and model from input or environment
            agent = IntelligentMCPAgent(
                api_key=input_data.get("openai_api_key"),
                base_url=input_data.get("openai_base_url")
            )
            
            # Step 1: Intelligent codebase analysis
            codebase_analysis = await agent.analyze_codebase_context(
                input_data["tree_structure"],
                input_data["analysis"], 
                input_data.get("important_files", [])
            )
            
            # Step 2: Generate MCP tools based on analysis
            mcp_tools = await agent.generate_mcp_tools(
                codebase_analysis,
                {
                    "project_name": input_data.get("project_name"),
                    "repo_id": input_data["repo_id"]
                }
            )
            
            # Step 3: Generate comprehensive documentation
            documentation = await agent.generate_documentation_resource(
                codebase_analysis,
                mcp_tools,
                {
                    "project_name": input_data.get("project_name"),
                    "repo_id": input_data["repo_id"]
                }
            )
            
            # Step 4: Generate deployable MCP server
            server_template = await agent.generate_mcp_server_template(
                mcp_tools,
                documentation, 
                {
                    "project_name": input_data.get("project_name"),
                    "repo_id": input_data["repo_id"]
                }
            )
            
            result = {
                "success": True,
                "repo_id": input_data["repo_id"],
                "codebase_analysis": codebase_analysis,
                "mcp_tools": mcp_tools,
                "documentation": documentation,
                "server_template": server_template,
                "summary": {
                    "api_endpoints": len(codebase_analysis.get("api_endpoints", [])),
                    "mcp_tools": len(mcp_tools),
                    "architecture": codebase_analysis.get("architecture_pattern"),
                    "technologies": codebase_analysis.get("main_technologies", [])
                }
            }
            
            print(json.dumps(result))
            
        except Exception as e:
            print(json.dumps({
                "success": False,
                "error": f"Analysis failed: {str(e)}"
            }), file=sys.stderr)
            sys.exit(1)
    
    else:
        print(json.dumps({
            "success": False,
            "error": f"Unknown command: {command}"
        }))
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())