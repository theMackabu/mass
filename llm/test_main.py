#!/usr/bin/env python3
"""
Pytest tests for main.py functions
"""

import pytest
import asyncio
import json
import sys
from pathlib import Path

# Add the current directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

from main import (
    detect_languages_from_files,
    generate_dockerfile_from_analysis,
    analyze_and_generate_tools,
    analyze_from_structured_data
)


class TestLanguageDetection:
    """Test language detection functionality"""
    
    def test_detect_javascript_files(self):
        """Test detection of JavaScript files"""
        files = {
            "app.js": "console.log('hello');",
            "index.js": "const express = require('express');",
            "test.jsx": "import React from 'react';"
        }
        languages = detect_languages_from_files(files)
        assert "JavaScript" in languages
    
    def test_detect_typescript_files(self):
        """Test detection of TypeScript files"""
        files = {
            "app.ts": "console.log('hello');",
            "index.tsx": "import React from 'react';"
        }
        languages = detect_languages_from_files(files)
        assert "TypeScript" in languages
    
    def test_detect_python_files(self):
        """Test detection of Python files"""
        files = {
            "main.py": "print('hello')",
            "test.py": "import pytest"
        }
        languages = detect_languages_from_files(files)
        assert "Python" in languages
    
    def test_detect_rust_files(self):
        """Test detection of Rust files"""
        files = {
            "main.rs": "fn main() { println!(\"hello\"); }",
            "lib.rs": "pub fn hello() {}"
        }
        languages = detect_languages_from_files(files)
        assert "Rust" in languages
    
    def test_detect_multiple_languages(self):
        """Test detection of multiple languages"""
        files = {
            "app.js": "console.log('hello');",
            "main.py": "print('hello')",
            "lib.rs": "fn main() {}",
            "index.ts": "const x: string = 'hello';"
        }
        languages = detect_languages_from_files(files)
        assert "JavaScript" in languages
        assert "Python" in languages
        assert "Rust" in languages
        assert "TypeScript" in languages
    
    def test_empty_files_dict(self):
        """Test with empty files dictionary"""
        languages = detect_languages_from_files({})
        assert languages == set()


class TestDockerfileGeneration:
    """Test Dockerfile generation functionality"""
    
    def test_generate_nodejs_dockerfile(self):
        """Test generation of Node.js Dockerfile"""
        analysis = {
            "languages": ["JavaScript"],
            "config_files": ["package.json"]
        }
        config_files = ["package.json"]
        
        dockerfile = generate_dockerfile_from_analysis(analysis, config_files)
        
        assert isinstance(dockerfile, str)
        assert "FROM node:" in dockerfile
        assert "WORKDIR" in dockerfile
        assert "COPY" in dockerfile
        assert "RUN" in dockerfile
        assert "EXPOSE" in dockerfile
        assert "CMD" in dockerfile
    
    def test_generate_rust_dockerfile(self):
        """Test generation of Rust Dockerfile"""
        analysis = {
            "languages": ["Rust"],
            "config_files": ["Cargo.toml"]
        }
        config_files = ["Cargo.toml"]
        
        dockerfile = generate_dockerfile_from_analysis(analysis, config_files)
        
        assert isinstance(dockerfile, str)
        assert "FROM rust:" in dockerfile
        assert "cargo build" in dockerfile
        assert "WORKDIR" in dockerfile
    
    def test_generate_python_dockerfile(self):
        """Test generation of Python Dockerfile"""
        analysis = {
            "languages": ["Python"],
            "config_files": ["requirements.txt"]
        }
        config_files = ["requirements.txt"]
        
        dockerfile = generate_dockerfile_from_analysis(analysis, config_files)
        
        assert isinstance(dockerfile, str)
        assert "FROM python:" in dockerfile
        assert "pip install" in dockerfile
        assert "WORKDIR" in dockerfile
    
    def test_generate_fallback_dockerfile(self):
        """Test generation of fallback Dockerfile"""
        analysis = {
            "languages": ["Unknown"],
            "config_files": []
        }
        config_files = []
        
        dockerfile = generate_dockerfile_from_analysis(analysis, config_files)
        
        assert isinstance(dockerfile, str)
        assert "FROM alpine:latest" in dockerfile
        assert "WORKDIR" in dockerfile


class TestAnalyzeAndGenerateTools:
    """Test the main analyze_and_generate_tools function"""
    
    @pytest.mark.asyncio
    async def test_analyze_simple_project(self):
        """Test analysis of a simple project"""
        files = {
            "package.json": json.dumps({
                "name": "test-project",
                "scripts": {"start": "node server.js"}
            }),
            "server.js": "const express = require('express');"
        }
        
        result = await analyze_and_generate_tools(
            repo_id="test-repo",
            files=files,
            project_name="Test Project"
        )
        
        assert result["success"] is True
        assert result["repo_id"] == "test-repo"
        assert "analysis" in result
        assert "mcp_tools" in result
        assert "dockerfile" in result
        assert isinstance(result["mcp_tools"], list)
        assert len(result["mcp_tools"]) > 0
    
    @pytest.mark.asyncio
    async def test_analyze_with_description(self):
        """Test analysis with project description"""
        files = {
            "main.py": "print('hello world')"
        }
        
        result = await analyze_and_generate_tools(
            repo_id="test-repo",
            files=files,
            project_name="Python Project",
            description="A simple Python application"
        )
        
        assert result["success"] is True
        assert "Python" in result["analysis"]["languages"]
    
    @pytest.mark.asyncio
    async def test_analyze_empty_files(self):
        """Test analysis with empty files"""
        result = await analyze_and_generate_tools(
            repo_id="test-repo",
            files={}
        )
        
        assert result["success"] is True
        assert result["analysis"]["total_files"] == 0


class TestStructuredDataAnalysis:
    """Test the structured data analysis function"""
    
    @pytest.mark.asyncio
    async def test_analyze_from_structured_data(self):
        """Test structured data analysis"""
        analysis = {
            "languages": ["JavaScript", "TypeScript"],
            "config_files": ["package.json", "tsconfig.json"],
            "file_count": 10,
            "size_bytes": 5000
        }
        
        tree_structure = """
project/
├── package.json
├── src/
│   ├── index.ts
│   └── app.js
└── README.md
"""
        
        result = await analyze_from_structured_data(
            repo_id="test-repo",
            project_name="Test Project",
            description="A test project",
            tree_structure=tree_structure,
            analysis=analysis,
            important_files=["package.json", "src/index.ts"],
            workspace_path="/tmp/test"
        )
        
        assert result["success"] is True
        assert result["repo_id"] == "test-repo"
        assert "mcp_tools" in result
        assert "dockerfile" in result
        assert "ai_analysis" in result
        assert isinstance(result["mcp_tools"], list)
        assert len(result["mcp_tools"]) > 0
    
    @pytest.mark.asyncio
    async def test_analyze_with_rust_analysis(self):
        """Test analysis with Rust-detected languages"""
        analysis = {
            "languages": ["Rust"],
            "config_files": ["Cargo.toml"],
            "file_count": 5
        }
        
        result = await analyze_from_structured_data(
            repo_id="rust-repo",
            project_name="Rust Project",
            description="A Rust project",
            tree_structure="project/\n├── Cargo.toml\n└── src/\n    └── main.rs",
            analysis=analysis,
            important_files=["Cargo.toml", "src/main.rs"],
            workspace_path="/tmp/rust"
        )
        
        assert result["success"] is True
        
        # Check that Rust-specific tools are generated
        tool_names = [tool["name"] for tool in result["mcp_tools"]]
        assert any("cargo" in name for name in tool_names)
    
    @pytest.mark.asyncio
    async def test_analyze_with_python_analysis(self):
        """Test analysis with Python-detected languages"""
        analysis = {
            "languages": ["Python"],
            "config_files": ["requirements.txt"],
            "file_count": 8
        }
        
        result = await analyze_from_structured_data(
            repo_id="python-repo",
            project_name="Python Project",
            description="A Python project",
            tree_structure="project/\n├── requirements.txt\n├── main.py\n└── tests/\n    └── test_main.py",
            analysis=analysis,
            important_files=["requirements.txt", "main.py"],
            workspace_path="/tmp/python"
        )
        
        assert result["success"] is True
        
        # Check that Python-specific tools are generated
        tool_names = [tool["name"] for tool in result["mcp_tools"]]
        assert any("python" in name for name in tool_names)


class TestMCPToolStructure:
    """Test MCP tool structure validation"""
    
    @pytest.mark.asyncio
    async def test_mcp_tool_required_fields(self):
        """Test that generated MCP tools have required fields"""
        files = {
            "package.json": json.dumps({"name": "test", "scripts": {"start": "node app.js"}}),
            "app.js": "const express = require('express');"
        }
        
        result = await analyze_and_generate_tools(
            repo_id="test-repo",
            files=files
        )
        
        tools = result["mcp_tools"]
        assert len(tools) > 0
        
        required_fields = ["name", "title", "description", "input_schema", "purpose", "implementation_hint"]
        
        for tool in tools:
            for field in required_fields:
                assert field in tool, f"Tool missing required field: {field}"
                assert tool[field] is not None, f"Tool field {field} should not be None"
                assert tool[field] != "", f"Tool field {field} should not be empty"
    
    @pytest.mark.asyncio
    async def test_mcp_tool_input_schema_type(self):
        """Test that input_schema is a dictionary"""
        files = {
            "main.py": "print('hello')"
        }
        
        result = await analyze_and_generate_tools(
            repo_id="test-repo",
            files=files
        )
        
        tools = result["mcp_tools"]
        
        for tool in tools:
            assert isinstance(tool["input_schema"], dict), "input_schema should be a dictionary"
    
    @pytest.mark.asyncio
    async def test_mcp_tool_name_format(self):
        """Test that tool names are properly formatted"""
        files = {
            "server.js": "const express = require('express');"
        }
        
        result = await analyze_and_generate_tools(
            repo_id="test-repo",
            files=files
        )
        
        tools = result["mcp_tools"]
        
        for tool in tools:
            name = tool["name"]
            assert isinstance(name, str), "Tool name should be a string"
            assert len(name) > 0, "Tool name should not be empty"
            # Tool names should be kebab-case or contain hyphens/underscores
            assert any(c in name for c in ['-', '_']) or name.islower(), f"Tool name '{name}' should be kebab-case or contain separators"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
