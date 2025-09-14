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

# Hardcoded environment variables
OPENAI_API_KEY = "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"
OPENAI_BASE_URL = "https://api.groq.com/openai/v1"
OPENAI_MODEL = "openai/gpt-oss-120b"

try:
    import openai
    from openai import AsyncOpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    print("Warning: OpenAI not available. Install with: uv pip install openai", file=sys.stderr)

class IntelligentMCPAgent:
    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None):
        self.api_key = api_key or OPENAI_API_KEY
        self.base_url = base_url or OPENAI_BASE_URL  # Allow custom base URL
        
        if not self.api_key:
            raise ValueError("OpenAI API key required.")
        
        # Initialize client with optional base_url
        client_kwargs = {"api_key": self.api_key}
        if self.base_url:
            client_kwargs["base_url"] = self.base_url
            print(f"Using custom OpenAI base URL: {self.base_url}", file=sys.stderr)
        
        self.client = AsyncOpenAI(**client_kwargs)
        
        # Model selection - defaults to Groq's fastest model
        self.model = OPENAI_MODEL  # Groq's fastest model for code analysis
        print(f"Using model: {self.model}", file=sys.stderr)
    
    def _extract_json_from_text(self, response_text: str) -> str:
        """Extract JSON from markdown code block or find JSON in text."""
        import re
        
        if not response_text:
            raise ValueError("Empty response from LLM")
        
        # First, try to extract JSON from markdown code blocks
        pattern = r'```(?:json)?\s*\n?(.*?)\n?\s*```'
        match = re.search(pattern, response_text.strip(), re.DOTALL | re.IGNORECASE)
        if match:
            return match.group(1).strip()
        
        # If no code blocks, try to find JSON in the text
        # Look for content that starts with { or [ and ends with } or ]
        json_pattern = r'(\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}|\[[^\[\]]*(?:\[[^\[\]]*\][^\[\]]*)*\])'
        json_matches = re.findall(json_pattern, response_text, re.DOTALL)
        
        if json_matches:
            # Use the first JSON-like content found
            return json_matches[0].strip()
        
        # Fallback to the original text
        return response_text.strip()

    def _extract_dockerfile_from_text(self, response_text: str) -> str:
        """Extract clean Dockerfile content from LLM response."""
        import re

        if not response_text:
            return ""

        # Remove any explanatory text before/after the Dockerfile
        lines = response_text.strip().split('\n')
        dockerfile_lines = []
        in_dockerfile = False

        # Look for the start of actual Dockerfile content
        for line in lines:
            stripped_line = line.strip()

            # Skip markdown code blocks
            if stripped_line.startswith('```'):
                continue

            # Skip common explanatory phrases
            if any(phrase in stripped_line.lower() for phrase in [
                'here is', 'here\'s', 'this dockerfile', 'the dockerfile',
                'below is', 'i\'ve created', 'i created', 'generated dockerfile',
                'dockerfile for', 'production-ready dockerfile'
            ]):
                continue

            # Start capturing when we see actual Dockerfile commands
            if stripped_line.startswith(('FROM ', 'RUN ', 'COPY ', 'ADD ', 'WORKDIR ',
                                       'EXPOSE ', 'CMD ', 'ENTRYPOINT ', 'ENV ', 'ARG ',
                                       'LABEL ', 'USER ', 'VOLUME ', 'HEALTHCHECK ')):
                in_dockerfile = True

            # Stop if we encounter explanatory text after Dockerfile content
            if in_dockerfile and stripped_line and not stripped_line.startswith('#') and \
               any(phrase in stripped_line.lower() for phrase in [
                   'this dockerfile', 'to build', 'to run', 'explanation:', 'note:',
                   'you can', 'make sure', 'remember to'
               ]):
                break

            # Capture Dockerfile lines (including comments and empty lines)
            if in_dockerfile:
                dockerfile_lines.append(line)

        # If no Dockerfile commands found, try extracting from code blocks
        if not dockerfile_lines:
            # Look for content between code blocks
            dockerfile_pattern = r'```(?:dockerfile|docker)?\s*\n?(.*?)\n?\s*```'
            match = re.search(dockerfile_pattern, response_text, re.DOTALL | re.IGNORECASE)
            if match:
                return match.group(1).strip()

            # Fallback: look for FROM command and take everything after it
            from_match = re.search(r'(FROM\s+.*?)(?:\n\n|\Z)', response_text, re.DOTALL | re.IGNORECASE)
            if from_match:
                return from_match.group(1).strip()

        return '\n'.join(dockerfile_lines).strip()

    async def select_important_files(self, tree_structure: str, analysis: Dict[str, Any], max_token_budget: int = 90000) -> List[str]:
        """
        Use LLM to intelligently select which files to analyze based on the tree structure
        """

        prompt = f"""
Analyze this project structure and select the most important files for understanding the codebase and generating MCP tools.

PROJECT INFO:
- Languages: {', '.join(analysis.get('languages', []))}
- File Count: {analysis.get('file_count', 0)}
- Config Files: {', '.join(analysis.get('config_files', []))}

PROJECT TREE:
{tree_structure}

Select 15-25 files that would be most valuable for:
1. Understanding the API endpoints and main functionality
2. Identifying business logic and data operations
3. Understanding project structure and architecture
4. Finding configuration and deployment info

Prioritize:
- Main entry points (main.*, index.*, app.*, server.*)
- API route files and controllers
- Core business logic files
- Database models and schemas
- Configuration files (package.json, requirements.txt, etc.)
- Important utility/helper files
- Documentation files (README.md, etc.)

Avoid:
- Test files (unless they reveal important API usage)
- Build/dist directories
- Node_modules or similar dependency folders
- Very large generated files
- Images, videos, or other binary assets

CRITICAL: Return ONLY a valid JSON array. Do not include any explanatory text, markdown formatting, code blocks, or additional content. Just the raw JSON array:
[
  "package.json",
  "src/index.js",
  "src/routes/api.js",
  "README.md"
]

Focus on files that will give the best understanding of what this project does and how it works.
"""

        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a senior software engineer analyzing codebases. CRITICAL: You must return ONLY a valid JSON array of file paths. No explanatory text, no markdown, no code blocks, no additional content. Just pure JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1  # Low temperature for consistent file selection
            )

            raw_response = response.choices[0].message.content
            if raw_response:
                cleaned_response = self._extract_json_from_text(raw_response)
                try:
                    selected_files = json.loads(cleaned_response)
                except json.JSONDecodeError as e:
                    print(f"JSON decode error in file selection. Raw response: {raw_response[:200]}...", file=sys.stderr)
                    print(f"Cleaned response: {cleaned_response[:200]}...", file=sys.stderr)
                    raise ValueError(f"Invalid JSON response from LLM: {e}")

                # Validate it's a list of strings
                if isinstance(selected_files, list) and all(isinstance(f, str) for f in selected_files):
                    print(f"LLM selected {len(selected_files)} files for analysis", file=sys.stderr)
                    return selected_files
                else:
                    raise ValueError("LLM returned invalid file list format")
            else:
                raise ValueError("Empty response from LLM")

        except Exception as e:
            print(f"Error in LLM file selection: {e}", file=sys.stderr)
            raise e


    def _estimate_tokens(self, text: str) -> int:
        """
        Rough token estimation (1 token ≈ 4 characters for English text, 1 token ≈ 1.2 characters for code)
        """
        # Code typically has more tokens per character than natural language
        return len(text) // 3  # Conservative estimate for mixed code/text

    def _truncate_files_to_token_budget(self, file_contents: List[str], token_budget: int = 90000) -> List[str]:
        """
        Truncate file contents to fit within token budget while preserving the most important parts
        """
        total_tokens = 0
        truncated_files = []

        for file_content in file_contents:
            if ':' not in file_content:
                continue

            filename, content = file_content.split(':', 1)
            content_tokens = self._estimate_tokens(content)

            if total_tokens + content_tokens <= token_budget:
                # File fits within budget
                truncated_files.append(file_content)
                total_tokens += content_tokens
            else:
                # Need to truncate this file
                remaining_budget = token_budget - total_tokens
                if remaining_budget > 100:  # Only include if we have meaningful space left
                    chars_to_keep = remaining_budget * 3  # Convert tokens back to chars

                    # Intelligent truncation - keep beginning and some end if possible
                    if len(content) > chars_to_keep:
                        if chars_to_keep > 1000:
                            # Keep first 80% and last 20%
                            keep_start = int(chars_to_keep * 0.8)
                            keep_end = int(chars_to_keep * 0.2)
                            truncated_content = (
                                content[:keep_start] +
                                f"\n\n... [Content truncated - {len(content)} total chars] ...\n\n" +
                                content[-keep_end:]
                            )
                        else:
                            # Just keep the beginning
                            truncated_content = content[:chars_to_keep] + f"\n... [Content truncated - {len(content)} total chars]"
                    else:
                        truncated_content = content

                    truncated_files.append(f"{filename}:{truncated_content}")
                    total_tokens = token_budget  # We're at budget limit
                    break
                else:
                    # No more room in budget
                    break

        print(f"Processed {len(truncated_files)} files within ~{total_tokens} token budget", file=sys.stderr)
        return truncated_files

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

CRITICAL: Return ONLY a valid JSON object. Do not include any explanatory text, markdown formatting, code blocks, or additional content. Just the raw JSON object:
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
                    {"role": "system", "content": "You are an expert software architect analyzing codebases. CRITICAL: You must return ONLY a valid JSON object. No explanatory text, no markdown, no code blocks, no additional content. Just pure JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3
            )
            
            raw_response = response.choices[0].message.content
            if raw_response:
                cleaned_response = self._extract_json_from_text(raw_response)
                try:
                    result = json.loads(cleaned_response)
                    return result
                except json.JSONDecodeError as e:
                    print(f"JSON decode error in codebase analysis. Raw response: {raw_response[:200]}...", file=sys.stderr)
                    print(f"Cleaned response: {cleaned_response[:200]}...", file=sys.stderr)
                    raise ValueError(f"Invalid JSON response from LLM: {e}")
            else:
                raise ValueError("Empty response from OpenAI")
            
        except Exception as e:
            print(f"Error in OpenAI analysis: {e}", file=sys.stderr)
            raise e

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

CRITICAL: Return ONLY a valid JSON array. Do not include any explanatory text, markdown formatting, code blocks, or additional content. Just the raw JSON array:
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
                    {"role": "system", "content": "You are an expert at creating practical developer tools. CRITICAL: You must return ONLY a valid JSON array. No explanatory text, no markdown, no code blocks, no additional content. Just pure JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7
            )
            
            raw_response = response.choices[0].message.content
            print(f"🤖 Raw LLM response for MCP tools: {raw_response[:300]}...", file=sys.stderr)
            if raw_response:
                cleaned_response = self._extract_json_from_text(raw_response)
                print(f"🧹 Cleaned response: {cleaned_response[:300]}...", file=sys.stderr)
                try:
                    tools = json.loads(cleaned_response)
                    print(f"✅ Successfully parsed {len(tools) if isinstance(tools, list) else 'unknown'} MCP tools", file=sys.stderr)
                    return tools
                except json.JSONDecodeError as e:
                    print(f"❌ JSON decode error in MCP tools generation. Raw response: {raw_response[:200]}...", file=sys.stderr)
                    print(f"🧹 Cleaned response: {cleaned_response[:200]}...", file=sys.stderr)
                    raise ValueError(f"Invalid JSON response from LLM: {e}")
            else:
                raise ValueError("Empty response from OpenAI")
            
        except Exception as e:
            print(f"Error generating MCP tools: {e}", file=sys.stderr)
            raise e

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

Return ONLY the documentation content. Do not include any explanatory text, additional formatting, or code blocks around the documentation. Just the raw markdown documentation.
"""

        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a technical writer creating developer documentation. CRITICAL: Return ONLY the documentation content. No explanatory text, no additional formatting, no code blocks around the content. Just the raw documentation."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.4
            )
            
            content = response.choices[0].message.content
            return content if content else ""
            
        except Exception as e:
            print(f"Error generating documentation: {e}", file=sys.stderr)
            raise e

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

CRITICAL: You must return ONLY a valid JSON object. Do not include any bash commands, explanatory text, markdown formatting, or code blocks. Just the raw JSON object with file contents as strings:

{{
  "package.json": "{{\\"name\\": \\"mcp-server\\", \\"version\\": \\"1.0.0\\"}}",
  "server.ts": "import {{ Server }} from '@modelcontextprotocol/sdk';",
  "Dockerfile": "FROM node:18-alpine",
  "README.md": "# MCP Server",
  "tsconfig.json": "{{\\"compilerOptions\\": {{}}}}"
}}
"""

        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an expert Node.js developer creating production-ready MCP servers. CRITICAL: You must return ONLY a valid JSON object with file contents. No explanatory text, no markdown, no code blocks, no additional content. Just pure JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3
            )
            
            raw_response = response.choices[0].message.content
            if raw_response:
                print(f"🔍 Raw server template response: {raw_response[:500]}...", file=sys.stderr)
                cleaned_response = self._extract_json_from_text(raw_response)
                print(f"🧹 Cleaned server template response: {cleaned_response[:500]}...", file=sys.stderr)
                try:
                    server_files = json.loads(cleaned_response)
                except json.JSONDecodeError as e:
                    print(f"❌ JSON decode error in server template generation. Raw response: {raw_response[:200]}...", file=sys.stderr)
                    print(f"🧹 Cleaned response: {cleaned_response[:200]}...", file=sys.stderr)
                    raise ValueError(f"Invalid JSON response from LLM: {e}")
            else:
                raise ValueError("Empty response from OpenAI")
            
            # Add the documentation as a separate file
            server_files["documentation.md"] = documentation
            
            return server_files
            
        except Exception as e:
            print(f"Error generating MCP server: {e}", file=sys.stderr)
            raise e

    async def generate_dockerfile_for_repository(self, files: Dict[str, str],
                                               file_structure: Dict[str, Any],
                                               api_endpoints: List[Dict[str, Any]],
                                               repo_metadata: Dict[str, Any]) -> str:
        """
        Generate a production-ready Dockerfile for a repository
        """

        # Analyze the project structure to determine the best Dockerfile approach
        languages = file_structure.get('languages', [])
        frameworks = file_structure.get('frameworks', [])
        has_package_json = file_structure.get('hasPackageJson', False)
        has_cargo_toml = file_structure.get('hasCargoToml', False)
        has_pyproject_toml = file_structure.get('hasPyprojectToml', False)
        has_dockerfile = file_structure.get('hasDockerfile', False)

        # Detect main language and framework
        primary_language = languages[0] if languages else "Unknown"
        primary_framework = frameworks[0] if frameworks else None

        prompt = f"""
Generate a production-ready Dockerfile for this project:

PROJECT INFO:
- Name: {repo_metadata.get('project_name', 'Unknown')}
- Languages: {', '.join(languages)}
- Frameworks: {', '.join(frameworks) if frameworks else 'None detected'}
- Has package.json: {has_package_json}
- Has Cargo.toml: {has_cargo_toml}
- Has pyproject.toml: {has_pyproject_toml}
- API Endpoints: {len(api_endpoints)}

DETECTED FILES (first few):
{chr(10).join([f"- {path}" for path in list(files.keys())[:10]])}

API ENDPOINTS:
{chr(10).join([f"- {ep.get('method', 'GET')} {ep.get('path', '/')}" for ep in api_endpoints[:5]])}

Generate a Dockerfile that:
1. Uses the appropriate base image for {primary_language}
2. Sets up the build environment correctly
3. Installs dependencies efficiently (layer caching)
4. Copies source code at the right time
5. Exposes appropriate ports based on detected endpoints
6. Sets up health checks
7. Uses security best practices (non-root user, etc.)
8. Optimizes for production deployment

Consider these frameworks: {', '.join(frameworks) if frameworks else 'None'}

CRITICAL: Your response must contain ONLY Dockerfile instructions. Start immediately with "FROM" and include only valid Dockerfile commands. No explanations, no markdown, no code blocks, no additional text:
"""

        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a DevOps engineer creating production-ready Dockerfiles. CRITICAL: You must respond with ONLY Dockerfile instructions (FROM, RUN, COPY, etc.). Do not include: explanatory text, markdown code blocks (```), comments about the dockerfile, build instructions, or any conversational text. Start your response directly with 'FROM' and include only valid Dockerfile commands."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2  # Lower temperature for more consistent infrastructure code
            )

            dockerfile_content = response.choices[0].message.content
            print(f"🐳 Raw Dockerfile response: {dockerfile_content[:200]}...", file=sys.stderr)

            if dockerfile_content:
                # Clean the response using robust text extraction
                cleaned_content = self._extract_dockerfile_from_text(dockerfile_content)
                print(f"🧹 Cleaned Dockerfile: {cleaned_content[:200]}...", file=sys.stderr)
                return cleaned_content
            else:
                return ""

        except Exception as e:
            print(f"Error generating Dockerfile: {e}", file=sys.stderr)
            raise e


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





# CLI Interface
async def main():
    if len(sys.argv) < 2:
        print(json.dumps({
            "error": "Usage: uv run agent.py <command>",
            "commands": ["analyze-and-generate", "select-files", "generate-dockerfile", "health-check"]
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

    if command == "select-files":
        if not OPENAI_AVAILABLE:
            print(json.dumps({
                "success": False,
                "error": "OpenAI library not available. Install with: uv pip install openai"
            }))
            sys.exit(1)

        try:
            # Read input from stdin
            input_data = json.loads(sys.stdin.read())

            # Create agent instance
            agent = IntelligentMCPAgent(
                api_key=input_data.get("openai_api_key"),
                base_url=input_data.get("openai_base_url")
            )

            # Select important files using LLM
            selected_files = await agent.select_important_files(
                input_data["tree_structure"],
                input_data["analysis"]
            )

            result = {
                "success": True,
                "selected_files": selected_files,
                "count": len(selected_files)
            }

            print(json.dumps(result))

        except Exception as e:
            print(json.dumps({
                "success": False,
                "error": f"File selection failed: {str(e)}"
            }), file=sys.stderr)
            sys.exit(1)

    elif command == "generate-dockerfile":
        if not OPENAI_AVAILABLE:
            print(json.dumps({
                "success": False,
                "error": "OpenAI library not available. Install with: uv pip install openai"
            }))
            sys.exit(1)

        try:
            # Read input from stdin
            input_data = json.loads(sys.stdin.read())

            # Create agent instance
            agent = IntelligentMCPAgent(
                api_key=input_data.get("openai_api_key"),
                base_url=input_data.get("openai_base_url")
            )

            # Generate Dockerfile based on project structure
            dockerfile_content = await agent.generate_dockerfile_for_repository(
                input_data.get("files", {}),
                input_data.get("file_structure", {}),
                input_data.get("api_endpoints", []),
                {
                    "project_name": input_data.get("project_name"),
                    "repo_id": input_data.get("repo_id"),
                    "description": input_data.get("description")
                }
            )

            result = {
                "success": True,
                "dockerfile": dockerfile_content
            }

            print(json.dumps(result))

        except Exception as e:
            print(json.dumps({
                "success": False,
                "error": f"Dockerfile generation failed: {str(e)}"
            }), file=sys.stderr)
            sys.exit(1)

    elif command == "analyze-and-generate":
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
            
            # Step 1: Use provided important files (already processed by Rust+LLM selection)
            important_files = input_data.get("important_files", [])

            # Step 2: Apply token budget truncation to ensure we don't exceed limits
            important_files = agent._truncate_files_to_token_budget(important_files, token_budget=90000)

            # Step 3: Intelligent codebase analysis with selected and truncated files
            codebase_analysis = await agent.analyze_codebase_context(
                input_data["tree_structure"],
                input_data["analysis"],
                important_files
            )
            
            # Step 4: Generate MCP tools based on analysis
            mcp_tools = await agent.generate_mcp_tools(
                codebase_analysis,
                {
                    "project_name": input_data.get("project_name"),
                    "repo_id": input_data["repo_id"]
                }
            )

            # Step 5: Generate comprehensive documentation
            documentation = await agent.generate_documentation_resource(
                codebase_analysis,
                mcp_tools,
                {
                    "project_name": input_data.get("project_name"),
                    "repo_id": input_data["repo_id"]
                }
            )

            # Note: Skip server template generation - using existing @llm/mcp_server_template/

            result = {
                "success": True,
                "repo_id": input_data["repo_id"],
                "codebase_analysis": codebase_analysis,
                "mcp_tools": mcp_tools,
                "documentation": documentation,
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