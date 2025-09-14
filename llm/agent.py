"""
MCP Tool Generation Agent

This module provides intelligent analysis of codebases to generate
contextually relevant MCP (Model Context Protocol) tools.
"""

import json
import os
import re
import asyncio
from pathlib import Path
from typing import Dict, List, Any, Optional, Set
from dataclasses import dataclass
from enum import Enum

import openai
from pydantic import BaseModel
import pathspec


class ProjectType(Enum):
    WEB_FRONTEND = "web_frontend"
    WEB_BACKEND = "web_backend"
    FULLSTACK = "fullstack"
    MOBILE = "mobile"
    DESKTOP = "desktop"
    CLI = "cli"
    LIBRARY = "library"
    MICROSERVICE = "microservice"
    DATA_SCIENCE = "data_science"
    UNKNOWN = "unknown"


class Language(Enum):
    JAVASCRIPT = "javascript"
    TYPESCRIPT = "typescript"
    PYTHON = "python"
    RUST = "rust"
    GO = "go"
    JAVA = "java"
    CPP = "cpp"
    CSHARP = "csharp"
    PHP = "php"
    RUBY = "ruby"


@dataclass
class FileInfo:
    path: str
    size: int
    content: str
    language: Optional[Language]
    importance_score: float
    file_type: str  # "config", "source", "test", "docs", etc.


@dataclass
class ProjectAnalysis:
    project_type: ProjectType
    primary_languages: List[Language]
    frameworks: List[str]
    key_files: List[FileInfo]
    api_endpoints: List[Dict[str, Any]]
    database_info: Optional[Dict[str, Any]]
    deployment_info: Dict[str, Any]
    file_tree: Dict[str, Any]
    confidence_score: float


class MCPTool(BaseModel):
    name: str
    title: str
    description: str
    input_schema: Dict[str, Any]
    purpose: str
    implementation_hint: str


class CodebaseAnalyzer:
    """Analyzes codebases to generate contextual MCP tools."""
    
    def __init__(self, openai_api_key: Optional[str] = None):
        self.openai_client = openai.AsyncOpenAI(
            api_key=openai_api_key or os.getenv("OPENAI_API_KEY")
        )
        
        # File patterns that are typically important for analysis
        self.important_patterns = {
            "config": {
                "package.json", "Cargo.toml", "pyproject.toml", "requirements.txt",
                "go.mod", "pom.xml", "build.gradle", "composer.json",
                "Dockerfile", "docker-compose.yml", ".env.example",
                "tsconfig.json", "webpack.config.js", "vite.config.js"
            },
            "entry_points": {
                "main.py", "main.rs", "main.go", "main.js", "index.js", "index.ts",
                "app.py", "server.js", "server.ts", "src/main.*", "src/index.*"
            },
            "api_routes": {
                "routes", "api", "endpoints", "handlers", "controllers", "views"
            },
            "models": {
                "models", "schema", "entities", "types", "structs"
            }
        }
        
        # Common gitignore patterns to skip
        self.ignore_patterns = pathspec.PathSpec.from_lines([
            "node_modules/", "target/", "__pycache__/", ".git/",
            "*.pyc", "*.pyo", "*.pyd", ".Python", "build/", "develop-eggs/",
            "dist/", "downloads/", "eggs/", ".eggs/", "lib/", "lib64/",
            "*.so", "*.dylib", "*.dll", ".venv/", "venv/", "ENV/",
            ".DS_Store", "Thumbs.db", "*.log", "*.tmp", "*.temp"
        ])

    def analyze_file_tree(self, files: Dict[str, str]) -> Dict[str, Any]:
        """Analyze the file tree structure to understand project organization."""
        tree = {}
        languages = set()
        
        for file_path in files.keys():
            if self.ignore_patterns.match_file(file_path):
                continue
                
            parts = file_path.split('/')
            current = tree
            
            for part in parts[:-1]:
                if part not in current:
                    current[part] = {}
                current = current[part]
            
            filename = parts[-1]
            current[filename] = {"type": "file", "path": file_path}
            
            # Detect language
            ext = Path(filename).suffix.lower()
            lang = self._detect_language(ext, filename)
            if lang:
                languages.add(lang)
        
        return {
            "structure": tree,
            "languages": list(languages),
            "total_files": len(files),
            "directories": self._count_directories(tree)
        }

    def _detect_language(self, extension: str, filename: str) -> Optional[Language]:
        """Detect programming language from file extension."""
        lang_map = {
            '.js': Language.JAVASCRIPT,
            '.mjs': Language.JAVASCRIPT,
            '.ts': Language.TYPESCRIPT,
            '.tsx': Language.TYPESCRIPT,
            '.jsx': Language.JAVASCRIPT,
            '.py': Language.PYTHON,
            '.rs': Language.RUST,
            '.go': Language.GO,
            '.java': Language.JAVA,
            '.cpp': Language.CPP,
            '.cc': Language.CPP,
            '.cxx': Language.CPP,
            '.cs': Language.CSHARP,
            '.php': Language.PHP,
            '.rb': Language.RUBY
        }
        return lang_map.get(extension)

    def _count_directories(self, tree: Dict) -> int:
        """Count directories in file tree."""
        count = 0
        for value in tree.values():
            if isinstance(value, dict) and value.get("type") != "file":
                count += 1 + self._count_directories(value)
        return count

    def select_key_files(self, files: Dict[str, str], max_files: int = 15) -> List[FileInfo]:
        """Intelligently select the most important files for analysis."""
        scored_files = []
        
        for file_path, content in files.items():
            if self.ignore_patterns.match_file(file_path):
                continue
                
            score = self._calculate_importance_score(file_path, content)
            if score > 0:
                lang = self._detect_language(Path(file_path).suffix.lower(), file_path)
                file_type = self._classify_file_type(file_path)
                
                scored_files.append(FileInfo(
                    path=file_path,
                    size=len(content),
                    content=content,
                    language=lang,
                    importance_score=score,
                    file_type=file_type
                ))
        
        # Sort by importance score and return top files
        scored_files.sort(key=lambda f: f.importance_score, reverse=True)
        return scored_files[:max_files]

    def _calculate_importance_score(self, file_path: str, content: str) -> float:
        """Calculate importance score for a file."""
        score = 0.0
        filename = Path(file_path).name.lower()
        
        # Configuration files are very important
        if any(pattern in filename for pattern in self.important_patterns["config"]):
            score += 10.0
        
        # Entry points are crucial
        if any(pattern in file_path.lower() for pattern in self.important_patterns["entry_points"]):
            score += 8.0
        
        # API-related files
        if any(pattern in file_path.lower() for pattern in self.important_patterns["api_routes"]):
            score += 7.0
        
        # Models/schemas
        if any(pattern in file_path.lower() for pattern in self.important_patterns["models"]):
            score += 6.0
        
        # README and documentation
        if filename.startswith("readme"):
            score += 5.0
        
        # Test files are somewhat important
        if "test" in file_path.lower() or "spec" in file_path.lower():
            score += 2.0
        
        # Penalize very large files (likely generated)
        if len(content) > 10000:
            score *= 0.5
        
        # Penalize very small files
        if len(content) < 50:
            score *= 0.3
        
        # Boost for files with imports/exports (likely important modules)
        if re.search(r'(import|export|require|from\s+\w+)', content[:1000]):
            score += 2.0
        
        # Boost for files with function/class definitions
        if re.search(r'(function|class|def|fn\s+\w+|func\s+\w+)', content[:1000]):
            score += 1.5
        
        return score

    def _classify_file_type(self, file_path: str) -> str:
        """Classify file type for better understanding."""
        filename = Path(file_path).name.lower()
        
        if any(pattern in filename for pattern in self.important_patterns["config"]):
            return "config"
        elif "test" in file_path.lower() or "spec" in file_path.lower():
            return "test"
        elif filename.startswith("readme") or filename.endswith(".md"):
            return "docs"
        elif any(pattern in file_path.lower() for pattern in self.important_patterns["api_routes"]):
            return "api"
        elif any(pattern in file_path.lower() for pattern in self.important_patterns["models"]):
            return "model"
        else:
            return "source"

    async def detect_project_type(self, key_files: List[FileInfo]) -> ProjectType:
        """Detect the type of project based on key files and content."""
        indicators = {
            ProjectType.WEB_FRONTEND: 0,
            ProjectType.WEB_BACKEND: 0,
            ProjectType.FULLSTACK: 0,
            ProjectType.MOBILE: 0,
            ProjectType.DESKTOP: 0,
            ProjectType.CLI: 0,
            ProjectType.LIBRARY: 0,
            ProjectType.MICROSERVICE: 0,
            ProjectType.DATA_SCIENCE: 0
        }
        
        for file_info in key_files:
            content_lower = file_info.content.lower()
            path_lower = file_info.path.lower()
            
            # Frontend indicators
            if any(term in content_lower for term in ['react', 'vue', 'angular', 'dom', 'document.']):
                indicators[ProjectType.WEB_FRONTEND] += 2
            
            # Backend indicators
            if any(term in content_lower for term in ['express', 'fastapi', 'django', 'flask', 'gin', 'echo']):
                indicators[ProjectType.WEB_BACKEND] += 2
            
            # Mobile indicators
            if any(term in content_lower for term in ['react-native', 'flutter', 'android', 'ios']):
                indicators[ProjectType.MOBILE] += 3
            
            # CLI indicators
            if any(term in content_lower for term in ['argparse', 'cobra', 'clap', 'commander']):
                indicators[ProjectType.CLI] += 2
            
            # Library indicators
            if 'lib' in path_lower or any(term in content_lower for term in ['export', 'module.exports']):
                indicators[ProjectType.LIBRARY] += 1
            
            # Data science indicators
            if any(term in content_lower for term in ['pandas', 'numpy', 'scikit', 'tensorflow', 'pytorch']):
                indicators[ProjectType.DATA_SCIENCE] += 3
        
        # Determine if fullstack
        if indicators[ProjectType.WEB_FRONTEND] > 0 and indicators[ProjectType.WEB_BACKEND] > 0:
            indicators[ProjectType.FULLSTACK] = indicators[ProjectType.WEB_FRONTEND] + indicators[ProjectType.WEB_BACKEND]
        
        # Return the type with highest score
        max_type = max(indicators.items(), key=lambda x: x[1])
        return max_type[0] if max_type[1] > 0 else ProjectType.UNKNOWN

    async def extract_api_endpoints(self, key_files: List[FileInfo]) -> List[Dict[str, Any]]:
        """Extract API endpoints from source files."""
        endpoints = []
        
        for file_info in key_files:
            if file_info.file_type != "api" and "api" not in file_info.path.lower():
                continue
                
            content = file_info.content
            
            # Express.js patterns
            express_patterns = [
                r'(?:app|router)\.(get|post|put|delete|patch)\s*\(\s*[\'"`]([^\'"`]+)[\'"`]',
                r'\.route\s*\(\s*[\'"`]([^\'"`]+)[\'"`]\s*\)\s*\.(get|post|put|delete|patch)'
            ]
            
            # FastAPI patterns
            fastapi_patterns = [
                r'@app\.(get|post|put|delete|patch)\s*\(\s*[\'"`]([^\'"`]+)[\'"`]'
            ]
            
            # Django patterns
            django_patterns = [
                r'path\s*\(\s*[\'"`]([^\'"`]+)[\'"`]'
            ]
            
            for pattern in express_patterns + fastapi_patterns + django_patterns:
                matches = re.finditer(pattern, content, re.IGNORECASE)
                for match in matches:
                    if len(match.groups()) == 2:
                        method, path = match.groups()
                        endpoints.append({
                            "method": method.upper(),
                            "path": path,
                            "file": file_info.path,
                            "framework": self._detect_framework(content)
                        })
        
        return endpoints

    def _detect_framework(self, content: str) -> str:
        """Detect web framework from content."""
        content_lower = content.lower()
        
        if 'express' in content_lower:
            return 'Express.js'
        elif 'fastapi' in content_lower:
            return 'FastAPI'
        elif 'django' in content_lower:
            return 'Django'
        elif 'flask' in content_lower:
            return 'Flask'
        elif 'next' in content_lower:
            return 'Next.js'
        elif 'react' in content_lower:
            return 'React'
        else:
            return 'Unknown'

    async def analyze_project(self, repo_id: str, files: Dict[str, str]) -> ProjectAnalysis:
        """Perform comprehensive project analysis."""
        # Step 1: Analyze file tree
        file_tree = self.analyze_file_tree(files)
        
        # Step 2: Select key files
        key_files = self.select_key_files(files)
        
        # Step 3: Detect project type
        project_type = await self.detect_project_type(key_files)
        
        # Step 4: Extract API endpoints
        api_endpoints = await self.extract_api_endpoints(key_files)
        
        # Step 5: Detect frameworks
        frameworks = list(set([
            self._detect_framework(f.content) for f in key_files
            if self._detect_framework(f.content) != 'Unknown'
        ]))
        
        return ProjectAnalysis(
            project_type=project_type,
            primary_languages=[Language(lang) for lang in file_tree["languages"]],
            frameworks=frameworks,
            key_files=key_files,
            api_endpoints=api_endpoints,
            database_info=None,  # TODO: Implement database detection
            deployment_info={},  # TODO: Implement deployment detection
            file_tree=file_tree,
            confidence_score=0.85  # TODO: Calculate actual confidence
        )

    async def generate_mcp_tools(self, analysis: ProjectAnalysis) -> List[MCPTool]:
        """Generate MCP tools based on project analysis."""
        
        # Create context for LLM
        context = self._build_context_for_llm(analysis)
        
        # Generate tools using OpenAI
        response = await self.openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system", 
                    "content": "You are an expert at creating MCP (Model Context Protocol) tools. Generate practical, useful tools based on codebase analysis."
                },
                {
                    "role": "user", 
                    "content": f"""
Based on this codebase analysis, generate 4-6 highly useful MCP tools:

{context}

Each tool should be practical and specific to this codebase. Return as JSON array with this structure:
{{
  "name": "kebab-case-name",
  "title": "Human Readable Title", 
  "description": "What this tool does",
  "input_schema": {{ "param1": "string", "param2": "number" }},
  "purpose": "Why this tool is useful for this specific codebase",
  "implementation_hint": "Brief hint on how to implement this tool"
}}

Focus on tools that would actually help developers working with this specific project.
"""
                }
            ],
            temperature=0.7
        )
        
        try:
            tools_data = json.loads(response.choices[0].message.content)
            return [MCPTool(**tool) for tool in tools_data]
        except (json.JSONDecodeError, KeyError) as e:
            # Fallback to basic tools if parsing fails
            return self._generate_fallback_tools(analysis)

    def _build_context_for_llm(self, analysis: ProjectAnalysis) -> str:
        """Build context string for LLM."""
        key_files_summary = "\n".join([
            f"- {f.path} ({f.file_type}): {len(f.content)} chars"
            for f in analysis.key_files[:10]
        ])
        
        api_summary = "\n".join([
            f"- {ep['method']} {ep['path']} ({ep['framework']})"
            for ep in analysis.api_endpoints[:10]
        ])
        
        return f"""
Project Type: {analysis.project_type.value}
Languages: {', '.join([lang.value for lang in analysis.primary_languages])}
Frameworks: {', '.join(analysis.frameworks)}
Total Files: {analysis.file_tree['total_files']}

Key Files:
{key_files_summary}

API Endpoints:
{api_summary or 'No API endpoints detected'}

Sample File Contents (first 500 chars):
{analysis.key_files[0].content[:500] if analysis.key_files else 'No files available'}
"""

    def _generate_fallback_tools(self, analysis: ProjectAnalysis) -> List[MCPTool]:
        """Generate basic fallback tools if LLM generation fails."""
        tools = []
        
        if analysis.api_endpoints:
            tools.append(MCPTool(
                name="test-api-endpoint",
                title="Test API Endpoint",
                description="Test any API endpoint in this project",
                input_schema={"method": "string", "path": "string", "body": "string"},
                purpose="Quickly test API endpoints",
                implementation_hint="Use HTTP client to make requests"
            ))
        
        if analysis.project_type in [ProjectType.WEB_FRONTEND, ProjectType.FULLSTACK]:
            tools.append(MCPTool(
                name="build-project",
                title="Build Project",
                description="Build the frontend project",
                input_schema={"environment": "string"},
                purpose="Build the project for deployment",
                implementation_hint="Run npm/yarn build commands"
            ))
        
        tools.append(MCPTool(
            name="analyze-dependencies",
            title="Analyze Dependencies",
            description="Analyze project dependencies and versions",
            input_schema={},
            purpose="Check for outdated or vulnerable dependencies",
            implementation_hint="Parse package files and check versions"
        ))
        
        return tools

    async def generate_dockerfile(self, analysis: ProjectAnalysis) -> str:
        """Generate a Dockerfile based on project analysis."""
        context = self._build_context_for_llm(analysis)
        
        response = await self.openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": "You are an expert at creating production-ready Dockerfiles. Create optimized, secure, multi-stage builds when appropriate."
                },
                {
                    "role": "user",
                    "content": f"""
Create a production-ready Dockerfile for this project:

{context}

Key Requirements:
1. Use appropriate base image for the detected languages/frameworks
2. Optimize for layer caching
3. Use multi-stage builds if beneficial
4. Set proper user permissions
5. Expose appropriate ports
6. Handle dependencies efficiently
7. Set appropriate working directory
8. Use .dockerignore patterns

Return only the Dockerfile content, no explanations.
"""
                }
            ],
            temperature=0.3
        )
        
        return response.choices[0].message.content


# Main interface function for the worker
async def analyze_and_generate_tools(repo_id: str, files: Dict[str, str], 
                                   project_name: Optional[str] = None,
                                   description: Optional[str] = None) -> Dict[str, Any]:
    """Main function to analyze codebase and generate MCP tools."""
    
    analyzer = CodebaseAnalyzer()
    
    try:
        # Analyze the project
        analysis = await analyzer.analyze_project(repo_id, files)
        
        # Generate MCP tools
        mcp_tools = await analyzer.generate_mcp_tools(analysis)
        
        # Generate Dockerfile
        dockerfile = await analyzer.generate_dockerfile(analysis)
        
        return {
            "success": True,
            "repo_id": repo_id,
            "analysis": {
                "project_type": analysis.project_type.value,
                "languages": [lang.value for lang in analysis.primary_languages],
                "frameworks": analysis.frameworks,
                "total_files": analysis.file_tree["total_files"],
                "key_files_count": len(analysis.key_files),
                "api_endpoints_count": len(analysis.api_endpoints),
                "confidence_score": analysis.confidence_score
            },
            "mcp_tools": [tool.dict() for tool in mcp_tools],
            "dockerfile": dockerfile,
            "key_files": [
                {
                    "path": f.path,
                    "type": f.file_type,
                    "language": f.language.value if f.language else None,
                    "importance_score": f.importance_score
                }
                for f in analysis.key_files
            ]
        }
    
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "repo_id": repo_id
        }


if __name__ == "__main__":
    # Test with sample data
    import asyncio
    
    sample_files = {
        "package.json": '{"name": "test-app", "dependencies": {"express": "^4.18.0"}}',
        "src/index.js": "const express = require('express'); const app = express(); app.get('/', (req, res) => res.send('Hello World'));"
    }
    
    async def test():
        result = await analyze_and_generate_tools("test-repo", sample_files)
        print(json.dumps(result, indent=2))
    
    asyncio.run(test())