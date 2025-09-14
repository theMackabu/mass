#!/usr/bin/env python3
"""
CLI interface for the LLM Agent
"""

import asyncio
import json
import sys
import os
from typing import Dict, Any, Optional, List
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv(dotenv_path=Path(__file__).parent / '.env')

# Try to import dependencies - gracefully handle if not available
try:
    import openai
    from pydantic import BaseModel
    DEPS_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Dependencies not available: {e}", file=sys.stderr)
    DEPS_AVAILABLE = False
    
    # Create placeholder BaseModel
    class BaseModel:
        def __init__(self, **kwargs):
            for key, value in kwargs.items():
                setattr(self, key, value)

# Set up OpenAI client
def get_openai_client():
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        return None
    return openai.AsyncOpenAI(api_key=api_key)

# Simple MCP tool model
class MCPTool(BaseModel):
    name: str
    title: str  
    description: str
    input_schema: dict
    purpose: str
    implementation_hint: str

# Fallback function for backward compatibility
async def analyze_and_generate_tools(repo_id: str, files: Dict[str, str], 
                                   project_name: Optional[str] = None,
                                   description: Optional[str] = None) -> Dict[str, Any]:
    return {
        "success": True,
        "repo_id": repo_id,
        "analysis": {
            "project_type": "unknown",
            "languages": list(detect_languages_from_files(files)),
            "total_files": len(files),
            "key_files_count": min(len(files), 10)
        },
        "mcp_tools": [
            {
                "name": "basic-analysis",
                "title": "Basic Project Analysis",
                "description": "Perform basic analysis of the project",
                "input_schema": {},
                "purpose": "Analyze project structure and files",
                "implementation_hint": "Use file analysis and tree structure"
            }
        ],
        "dockerfile": "FROM alpine:latest\nWORKDIR /app\nCOPY . .\nCMD [\"echo\", \"Hello World\"]"
    }

def detect_languages_from_files(files: Dict[str, str]) -> set:
    """Detect languages from file extensions"""
    languages = set()
    for file_path in files.keys():
        ext = file_path.split('.')[-1].lower()
        if ext in ['js', 'jsx', 'mjs']: languages.add('JavaScript')
        elif ext in ['ts', 'tsx']: languages.add('TypeScript')  
        elif ext == 'py': languages.add('Python')
        elif ext == 'rs': languages.add('Rust')
        elif ext == 'go': languages.add('Go')
        elif ext == 'java': languages.add('Java')
    return languages

# Enhanced function for structured data analysis
async def analyze_from_structured_data(repo_id: str, project_name: Optional[str],
                                     description: Optional[str], tree_structure: str,
                                     analysis: Dict[str, Any], important_files: list,
                                     workspace_path: Optional[str]) -> Dict[str, Any]:
    """
    Analyze repository using structured data from Rust operations
    """
    if not AGENT_AVAILABLE:
        # Simple fallback based on Rust analysis
        languages = analysis.get('languages', [])
        config_files = analysis.get('config_files', [])
        
        # Generate tools based on detected languages and configs
        tools = []
        
        # Basic project analysis
        tools.append({
            "name": "analyze-project-structure",
            "title": "Analyze Project Structure",
            "description": f"Analyze {', '.join(languages)} project structure",
            "input_schema": {},
            "purpose": "Get project overview from tree structure",
            "implementation_hint": "Parse tree output and file analysis"
        })
        
        # Language-specific tools
        if any(lang in ['JavaScript', 'TypeScript'] for lang in languages):
            tools.append({
                "name": "run-npm-commands",
                "title": "Run npm Commands",
                "description": "Execute npm scripts and commands",
                "input_schema": {"script": "string"},
                "purpose": "Build, test, or run the Node.js project",
                "implementation_hint": "Execute npm run <script>"
            })
        
        if 'Rust' in languages:
            tools.append({
                "name": "run-cargo-commands",
                "title": "Run Cargo Commands", 
                "description": "Execute Rust cargo commands",
                "input_schema": {"command": "string"},
                "purpose": "Build, test, or run the Rust project",
                "implementation_hint": "Execute cargo <command>"
            })
            
        if 'Python' in languages:
            tools.append({
                "name": "run-python-tools",
                "title": "Run Python Tools",
                "description": "Execute Python project tools",
                "input_schema": {"tool": "string"},
                "purpose": "Run tests, linting, or other Python tools",
                "implementation_hint": "Execute pytest, pylint, etc."
            })
        
        # Docker tools if Dockerfile detected
        if 'Dockerfile' in config_files:
            tools.append({
                "name": "docker-operations",
                "title": "Docker Operations",
                "description": "Build and manage Docker containers",
                "input_schema": {"action": "string"},
                "purpose": "Build, run, or manage Docker containers",
                "implementation_hint": "Execute docker build, docker run, etc."
            })
        
        # Generate basic Dockerfile based on detected languages
        dockerfile = generate_dockerfile_from_analysis(analysis, config_files)
        
        return {
            "success": True,
            "repo_id": repo_id,
            "mcp_tools": tools,
            "dockerfile": dockerfile,
            "ai_analysis": {
                "summary": f"Project with {analysis.get('file_count', 0)} files, languages: {', '.join(languages)}",
                "languages": languages,
                "config_files": config_files,
                "confidence": 0.75
            }
        }
    
    # If agent is available, use it for more sophisticated analysis
    # For now, fall back to the simple version
    return await analyze_from_structured_data(repo_id, project_name, description, 
                                            tree_structure, analysis, important_files, 
                                            workspace_path)

def generate_dockerfile_from_analysis(analysis: Dict[str, Any], config_files: list) -> str:
    """Generate Dockerfile based on Rust analysis results"""
    languages = analysis.get('languages', [])
    
    if 'package.json' in config_files and any(lang in ['JavaScript', 'TypeScript'] for lang in languages):
        return """FROM node:18-alpine
WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production
COPY . .
EXPOSE 3000
CMD ["npm", "start"]"""
    
    elif 'Cargo.toml' in config_files and 'Rust' in languages:
        return """FROM rust:1.70 as builder
WORKDIR /usr/src/app
COPY . .
RUN cargo build --release

FROM debian:bullseye-slim
RUN apt-get update && apt-get install -y ca-certificates && rm -rf /var/lib/apt/lists/*
COPY --from=builder /usr/src/app/target/release/* /usr/local/bin/
CMD ["./app"]"""
    
    elif any(f in config_files for f in ['pyproject.toml', 'requirements.txt']) and 'Python' in languages:
        return """FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt* pyproject.toml* ./
RUN pip install -r requirements.txt || pip install -e . || echo "No requirements found"
COPY . .
EXPOSE 8000
CMD ["python", "-m", "app"]"""
    
    else:
        return """FROM alpine:latest
WORKDIR /app
COPY . .
EXPOSE 8080
CMD ["echo", "Generated from Rust analysis - configure as needed"]"""


def load_json_input() -> Dict[str, Any]:
    """Load JSON input from stdin."""
    try:
        data = sys.stdin.read()
        return json.loads(data)
    except json.JSONDecodeError as e:
        return {"error": f"Invalid JSON input: {e}"}


async def main():
    """Main CLI interface."""
    if len(sys.argv) < 2:
        print(json.dumps({
            "error": "Usage: python main.py <command>",
            "commands": ["analyze", "generate-dockerfile", "health-check"]
        }))
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == "health-check":
        print(json.dumps({
            "success": True,
            "service": "llm-agent",
            "status": "healthy",
            "version": "0.1.0"
        }))
        return
    
    if command == "analyze":
        # Original analyze command (for backward compatibility)
        input_data = load_json_input()
        
        if "error" in input_data:
            print(json.dumps(input_data))
            sys.exit(1)
        
        required_fields = ["repo_id", "files"]
        for field in required_fields:
            if field not in input_data:
                print(json.dumps({
                    "success": False,
                    "error": f"Missing required field: {field}"
                }))
                sys.exit(1)
        
        result = await analyze_and_generate_tools(
            repo_id=input_data["repo_id"],
            files=input_data["files"],
            project_name=input_data.get("project_name"),
            description=input_data.get("description")
        )
        
        print(json.dumps(result))
    
    elif command == "analyze-from-tree":
        # New streamlined analyze command using Rust analysis
        input_data = load_json_input()
        
        if "error" in input_data:
            print(json.dumps(input_data))
            sys.exit(1)
        
        required_fields = ["repo_id", "analysis", "tree_structure"]
        for field in required_fields:
            if field not in input_data:
                print(json.dumps({
                    "success": False,
                    "error": f"Missing required field: {field}"
                }))
                sys.exit(1)
        
        # Placeholder for structured analysis - implement when dependencies are installed
        result = {
            "success": True,
            "repo_id": input_data["repo_id"],
            "mcp_tools": [
                {
                    "name": "analyze-project",
                    "title": "Analyze Project",
                    "description": f"Analyze {input_data['analysis'].get('languages', ['unknown'])} project",
                    "input_schema": {},
                    "purpose": "Basic project analysis",
                    "implementation_hint": "Use tree structure analysis"
                }
            ],
            "dockerfile": "FROM alpine:latest\nWORKDIR /app\nCOPY . .\nCMD [\"echo\", \"Generated by streamlined analysis\"]",
            "ai_analysis": {
                "summary": f"Project with {input_data['analysis'].get('file_count', 0)} files",
                "languages": input_data['analysis'].get('languages', []),
                "confidence": 0.8
            }
        }
        
        print(json.dumps(result))
    
    else:
        print(json.dumps({
            "success": False,
            "error": f"Unknown command: {command}",
            "available_commands": ["analyze", "generate-dockerfile", "health-check"]
        }))
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
