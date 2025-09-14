#!/usr/bin/env python3
"""
Pytest tests for agent.py functions
"""

import pytest
import asyncio
import json
import sys
import os
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock

# Add the current directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

try:
    from agent import IntelligentMCPAgent
    AGENT_AVAILABLE = True
except ImportError:
    AGENT_AVAILABLE = False
    print("Warning: agent.py not available for testing")


@pytest.mark.skipif(not AGENT_AVAILABLE, reason="agent.py not available")
class TestIntelligentMCPAgent:
    """Test IntelligentMCPAgent class"""
    
    def test_agent_initialization_with_api_key(self):
        """Test agent initialization with API key"""
        agent = IntelligentMCPAgent(api_key="test-key")
        assert agent.api_key == "test-key"
        assert agent.client is not None
    
    def test_agent_initialization_without_api_key(self):
        """Test agent initialization without API key should raise error"""
        with pytest.raises(ValueError, match="OpenAI API key required"):
            IntelligentMCPAgent(api_key=None)
    
    def test_agent_initialization_with_base_url(self):
        """Test agent initialization with custom base URL"""
        agent = IntelligentMCPAgent(
            api_key="test-key",
            base_url="https://api.example.com/v1"
        )
        assert agent.base_url == "https://api.example.com/v1"
    
    def test_agent_model_selection(self):
        """Test agent model selection"""
        agent = IntelligentMCPAgent(api_key="test-key")
        assert agent.model is not None
        assert isinstance(agent.model, str)
    
    def test_clean_json_response_with_markdown(self):
        """Test JSON response cleaning with markdown code blocks"""
        agent = IntelligentMCPAgent(api_key="test-key")
        
        # Test with markdown code block
        response = '```json\n{"test": "value"}\n```'
        cleaned = agent._clean_json_response(response)
        assert cleaned == '{"test": "value"}'
        
        # Test with json code block
        response = '```json\n{"test": "value"}\n```'
        cleaned = agent._clean_json_response(response)
        assert cleaned == '{"test": "value"}'
    
    def test_clean_json_response_without_markdown(self):
        """Test JSON response cleaning without markdown"""
        agent = IntelligentMCPAgent(api_key="test-key")
        
        response = '{"test": "value"}'
        cleaned = agent._clean_json_response(response)
        assert cleaned == '{"test": "value"}'
    
    def test_clean_json_response_empty(self):
        """Test JSON response cleaning with empty response"""
        agent = IntelligentMCPAgent(api_key="test-key")
        
        with pytest.raises(ValueError, match="Empty response from LLM"):
            agent._clean_json_response("")
        
        with pytest.raises(ValueError, match="Empty response from LLM"):
            agent._clean_json_response(None)
    
    def test_estimate_tokens(self):
        """Test token estimation"""
        agent = IntelligentMCPAgent(api_key="test-key")
        
        # Test with simple text
        text = "Hello world"
        tokens = agent._estimate_tokens(text)
        assert isinstance(tokens, int)
        assert tokens > 0
        
        # Test with longer text
        long_text = "Hello world " * 100
        long_tokens = agent._estimate_tokens(long_text)
        assert long_tokens > tokens
    
    def test_truncate_files_to_token_budget(self):
        """Test file truncation to fit token budget"""
        agent = IntelligentMCPAgent(api_key="test-key")
        
        # Create sample file contents
        files = [
            "file1.js:console.log('hello');",
            "file2.js:" + "console.log('test');" * 1000,  # Large file
            "file3.js:const x = 1;"
        ]
        
        truncated = agent._truncate_files_to_token_budget(files, token_budget=1000)
        
        assert isinstance(truncated, list)
        assert len(truncated) <= len(files)
        
        # Check that files are properly formatted
        for file_content in truncated:
            assert ':' in file_content, "File content should contain filename:content format"
    
    def test_build_analysis_context(self):
        """Test building analysis context"""
        agent = IntelligentMCPAgent(api_key="test-key")
        
        tree_structure = "project/\n├── file1.js\n└── file2.py"
        analysis = {
            "languages": ["JavaScript", "Python"],
            "config_files": ["package.json"],
            "file_count": 2,
            "size_bytes": 1000
        }
        important_files = [
            "file1.js:console.log('hello');",
            "file2.py:print('world')"
        ]
        
        context = agent._build_analysis_context(tree_structure, analysis, important_files)
        
        assert isinstance(context, str)
        assert "PROJECT STRUCTURE:" in context
        assert "BASIC ANALYSIS:" in context
        assert "JavaScript" in context
        assert "Python" in context
        assert "file1.js" in context
        assert "file2.py" in context


@pytest.mark.skipif(not AGENT_AVAILABLE, reason="agent.py not available")
class TestAgentWithMockedOpenAI:
    """Test agent with mocked OpenAI responses"""
    
    @pytest.fixture
    def mock_openai_response(self):
        """Mock OpenAI response"""
        mock_response = Mock()
        mock_choice = Mock()
        mock_choice.message.content = '["file1.js", "file2.py", "package.json"]'
        mock_response.choices = [mock_choice]
        return mock_response
    
    @pytest.mark.asyncio
    async def test_select_important_files(self, mock_openai_response):
        """Test file selection with mocked OpenAI"""
        agent = IntelligentMCPAgent(api_key="test-key")
        
        tree_structure = "project/\n├── file1.js\n├── file2.py\n└── package.json"
        analysis = {
            "languages": ["JavaScript", "Python"],
            "file_count": 3,
            "config_files": ["package.json"]
        }
        
        with patch.object(agent.client.chat.completions, 'create', new_callable=AsyncMock) as mock_create:
            mock_create.return_value = mock_openai_response
            
            selected_files = await agent.select_important_files(tree_structure, analysis)
            
            assert isinstance(selected_files, list)
            assert len(selected_files) > 0
            assert all(isinstance(f, str) for f in selected_files)
    
    @pytest.mark.asyncio
    async def test_select_important_files_invalid_json(self):
        """Test file selection with invalid JSON response"""
        agent = IntelligentMCPAgent(api_key="test-key")
        
        # Mock response with invalid JSON
        mock_response = Mock()
        mock_choice = Mock()
        mock_choice.message.content = "This is not JSON"
        mock_response.choices = [mock_choice]
        
        tree_structure = "project/\n├── file1.js"
        analysis = {"languages": ["JavaScript"], "file_count": 1}
        
        with patch.object(agent.client.chat.completions, 'create', new_callable=AsyncMock) as mock_create:
            mock_create.return_value = mock_response
            
            with pytest.raises(ValueError, match="Invalid JSON response from LLM"):
                await agent.select_important_files(tree_structure, analysis)
    
    @pytest.mark.asyncio
    async def test_analyze_codebase_context(self):
        """Test codebase analysis with mocked OpenAI"""
        agent = IntelligentMCPAgent(api_key="test-key")
        
        # Mock response for codebase analysis
        mock_response = Mock()
        mock_choice = Mock()
        mock_choice.message.content = json.dumps({
            "api_endpoints": [
                {
                    "method": "GET",
                    "path": "/api/users",
                    "function": "getUsers",
                    "description": "Get all users",
                    "parameters": [],
                    "file": "server.js"
                }
            ],
            "key_functions": [
                {
                    "name": "getUsers",
                    "description": "Retrieve all users",
                    "file": "server.js",
                    "type": "business_logic"
                }
            ],
            "database_operations": [],
            "external_integrations": [],
            "project_summary": "A simple API server",
            "architecture_pattern": "REST API",
            "main_technologies": ["Express.js", "Node.js"]
        })
        mock_response.choices = [mock_choice]
        
        tree_structure = "project/\n├── server.js"
        analysis = {"languages": ["JavaScript"], "file_count": 1}
        important_files = ["server.js:const express = require('express');"]
        
        with patch.object(agent.client.chat.completions, 'create', new_callable=AsyncMock) as mock_create:
            mock_create.return_value = mock_response
            
            result = await agent.analyze_codebase_context(tree_structure, analysis, important_files)
            
            assert isinstance(result, dict)
            assert "api_endpoints" in result
            assert "key_functions" in result
            assert "project_summary" in result
            assert "architecture_pattern" in result
            assert "main_technologies" in result
    
    @pytest.mark.asyncio
    async def test_generate_mcp_tools(self):
        """Test MCP tools generation with mocked OpenAI"""
        agent = IntelligentMCPAgent(api_key="test-key")
        
        # Mock response for MCP tools generation
        mock_response = Mock()
        mock_choice = Mock()
        mock_choice.message.content = json.dumps([
            {
                "name": "get-users",
                "title": "Get Users",
                "description": "Retrieve all users from the API",
                "input_schema": {},
                "category": "api",
                "implementation": {
                    "type": "http_request",
                    "endpoint": "/api/users",
                    "method": "GET",
                    "example_usage": "Call GET /api/users"
                },
                "purpose": "Test the users API endpoint"
            }
        ])
        mock_response.choices = [mock_choice]
        
        codebase_analysis = {
            "api_endpoints": [
                {
                    "method": "GET",
                    "path": "/api/users",
                    "function": "getUsers",
                    "description": "Get all users"
                }
            ],
            "project_summary": "A simple API server",
            "architecture_pattern": "REST API",
            "main_technologies": ["Express.js"]
        }
        
        repo_metadata = {
            "project_name": "Test Project",
            "repo_id": "test-repo"
        }
        
        with patch.object(agent.client.chat.completions, 'create', new_callable=AsyncMock) as mock_create:
            mock_create.return_value = mock_response
            
            tools = await agent.generate_mcp_tools(codebase_analysis, repo_metadata)
            
            assert isinstance(tools, list)
            assert len(tools) > 0
            
            tool = tools[0]
            required_fields = ["name", "title", "description", "input_schema", "category", "implementation", "purpose"]
            for field in required_fields:
                assert field in tool
    
    @pytest.mark.asyncio
    async def test_generate_documentation_resource(self):
        """Test documentation generation with mocked OpenAI"""
        agent = IntelligentMCPAgent(api_key="test-key")
        
        # Mock response for documentation generation
        mock_response = Mock()
        mock_choice = Mock()
        mock_choice.message.content = "# Test Project - Developer Guide\n\n## Project Overview\nThis is a test project."
        mock_response.choices = [mock_choice]
        
        codebase_analysis = {
            "project_summary": "A test project",
            "architecture_pattern": "REST API"
        }
        
        mcp_tools = [
            {
                "name": "test-tool",
                "title": "Test Tool",
                "description": "A test tool"
            }
        ]
        
        repo_metadata = {
            "project_name": "Test Project",
            "repo_id": "test-repo"
        }
        
        with patch.object(agent.client.chat.completions, 'create', new_callable=AsyncMock) as mock_create:
            mock_create.return_value = mock_response
            
            documentation = await agent.generate_documentation_resource(
                codebase_analysis, mcp_tools, repo_metadata
            )
            
            assert isinstance(documentation, str)
            assert "Test Project" in documentation
            assert "Developer Guide" in documentation
    
    @pytest.mark.asyncio
    async def test_generate_mcp_server_template(self):
        """Test MCP server template generation with mocked OpenAI"""
        agent = IntelligentMCPAgent(api_key="test-key")
        
        # Mock response for server template generation
        mock_response = Mock()
        mock_choice = Mock()
        mock_choice.message.content = json.dumps({
            "package.json": '{"name": "test-mcp-server", "version": "1.0.0"}',
            "server.ts": "import { Server } from '@modelcontextprotocol/sdk';",
            "Dockerfile": "FROM node:18-alpine",
            "README.md": "# Test MCP Server",
            "tsconfig.json": '{"compilerOptions": {"target": "ES2020"}}'
        })
        mock_response.choices = [mock_choice]
        
        mcp_tools = [
            {
                "name": "test-tool",
                "title": "Test Tool",
                "description": "A test tool"
            }
        ]
        
        documentation = "# Test Documentation"
        
        repo_metadata = {
            "project_name": "Test Project",
            "repo_id": "test-repo"
        }
        
        with patch.object(agent.client.chat.completions, 'create', new_callable=AsyncMock) as mock_create:
            mock_create.return_value = mock_response
            
            server_template = await agent.generate_mcp_server_template(
                mcp_tools, documentation, repo_metadata
            )
            
            assert isinstance(server_template, dict)
            assert "package.json" in server_template
            assert "server.ts" in server_template
            assert "Dockerfile" in server_template
            assert "README.md" in server_template
            assert "documentation.md" in server_template  # Added by the method
    
    @pytest.mark.asyncio
    async def test_generate_dockerfile_for_repository(self):
        """Test Dockerfile generation for repository with mocked OpenAI"""
        agent = IntelligentMCPAgent(api_key="test-key")
        
        # Mock response for Dockerfile generation
        mock_response = Mock()
        mock_choice = Mock()
        mock_choice.message.content = """FROM node:18-alpine
WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production
COPY . .
EXPOSE 3000
CMD ["npm", "start"]"""
        mock_response.choices = [mock_choice]
        
        files = {
            "package.json": '{"name": "test", "scripts": {"start": "node server.js"}}',
            "server.js": "console.log('hello');"
        }
        
        file_structure = {
            "languages": ["JavaScript"],
            "frameworks": ["Express.js"],
            "hasPackageJson": True
        }
        
        api_endpoints = [
            {"method": "GET", "path": "/api/users"}
        ]
        
        repo_metadata = {
            "project_name": "Test Project",
            "repo_id": "test-repo"
        }
        
        with patch.object(agent.client.chat.completions, 'create', new_callable=AsyncMock) as mock_create:
            mock_create.return_value = mock_response
            
            dockerfile = await agent.generate_dockerfile_for_repository(
                files, file_structure, api_endpoints, repo_metadata
            )
            
            assert isinstance(dockerfile, str)
            assert "FROM node:" in dockerfile
            assert "WORKDIR" in dockerfile
            assert "COPY" in dockerfile
            assert "RUN" in dockerfile
            assert "EXPOSE" in dockerfile
            assert "CMD" in dockerfile


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
