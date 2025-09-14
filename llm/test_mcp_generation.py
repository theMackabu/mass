#!/usr/bin/env python3
"""
Test script for LLM MCP server generation logic

This script tests the MCP tool generation functionality by:
1. Testing the main.py CLI interface
2. Testing the agent.py intelligent analysis
3. Validating MCP tool generation
4. Testing Dockerfile generation
5. Running integration tests
"""

import asyncio
import json
import sys
import os
import tempfile
import subprocess
from pathlib import Path
from typing import Dict, Any, List
# import pytest  # Only needed for pytest tests, not for this script

# Add the current directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

# Import the modules we want to test
try:
    from main import (
        analyze_and_generate_tools,
        analyze_from_structured_data,
        generate_dockerfile_from_analysis,
        detect_languages_from_files,
        load_json_input
    )
    from agent import IntelligentMCPAgent
    MODULES_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Could not import modules: {e}")
    MODULES_AVAILABLE = False


class MCPTestRunner:
    """Test runner for MCP generation functionality"""
    
    def __init__(self):
        self.test_results = []
        self.temp_dir = None
        
    def setup_test_environment(self):
        """Set up test environment with sample data"""
        self.temp_dir = tempfile.mkdtemp(prefix="mcp_test_")
        print(f"Test environment: {self.temp_dir}")
        
        # Create sample test data
        self.sample_files = {
            "package.json": json.dumps({
                "name": "test-project",
                "version": "1.0.0",
                "scripts": {
                    "start": "node server.js",
                    "test": "jest",
                    "build": "webpack"
                },
                "dependencies": {
                    "express": "^4.18.0",
                    "mongoose": "^7.0.0"
                }
            }),
            "server.js": """
const express = require('express');
const mongoose = require('mongoose');

const app = express();
const PORT = process.env.PORT || 3000;

// Connect to MongoDB
mongoose.connect(process.env.MONGODB_URI || 'mongodb://localhost:27017/testdb');

// User schema
const userSchema = new mongoose.Schema({
  name: String,
  email: String,
  createdAt: { type: Date, default: Date.now }
});

const User = mongoose.model('User', userSchema);

// Routes
app.get('/api/users', async (req, res) => {
  try {
    const users = await User.find();
    res.json(users);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

app.post('/api/users', async (req, res) => {
  try {
    const user = new User(req.body);
    await user.save();
    res.status(201).json(user);
  } catch (error) {
    res.status(400).json({ error: error.message });
  }
});

app.get('/api/users/:id', async (req, res) => {
  try {
    const user = await User.findById(req.params.id);
    if (!user) return res.status(404).json({ error: 'User not found' });
    res.json(user);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

app.listen(PORT, () => {
  console.log(`Server running on port ${PORT}`);
});
""",
            "README.md": """
# Test Project

A simple Express.js API with MongoDB integration.

## Features
- User management API
- MongoDB integration
- RESTful endpoints

## API Endpoints
- GET /api/users - List all users
- POST /api/users - Create a new user
- GET /api/users/:id - Get user by ID
""",
            "Dockerfile": """
FROM node:18-alpine
WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production
COPY . .
EXPOSE 3000
CMD ["npm", "start"]
"""
        }
        
        # Create sample analysis data
        self.sample_analysis = {
            "languages": ["JavaScript", "JSON"],
            "config_files": ["package.json", "Dockerfile"],
            "file_count": 4,
            "size_bytes": 2048,
            "frameworks": ["Express.js"],
            "hasPackageJson": True,
            "hasDockerfile": True
        }
        
        # Create sample tree structure
        self.sample_tree = """
test-project/
├── package.json
├── server.js
├── README.md
└── Dockerfile
"""
        
        # Create sample important files (formatted as expected by agent)
        self.sample_important_files = [
            f"package.json:{self.sample_files['package.json']}",
            f"server.js:{self.sample_files['server.js']}",
            f"README.md:{self.sample_files['README.md']}"
        ]
    
    def cleanup_test_environment(self):
        """Clean up test environment"""
        if self.temp_dir and os.path.exists(self.temp_dir):
            import shutil
            shutil.rmtree(self.temp_dir)
            print(f"Cleaned up test environment: {self.temp_dir}")
    
    def run_test(self, test_name: str, test_func):
        """Run a single test and record results"""
        print(f"\n🧪 Running test: {test_name}")
        try:
            result = test_func()
            self.test_results.append({
                "name": test_name,
                "status": "PASS",
                "result": result
            })
            print(f"✅ {test_name}: PASSED")
            return True
        except Exception as e:
            self.test_results.append({
                "name": test_name,
                "status": "FAIL",
                "error": str(e)
            })
            print(f"❌ {test_name}: FAILED - {e}")
            return False
    
    def test_language_detection(self):
        """Test language detection from files"""
        if not MODULES_AVAILABLE:
            raise ImportError("Required modules not available")
        
        languages = detect_languages_from_files(self.sample_files)
        expected = {"JavaScript", "JSON"}
        
        if languages != expected:
            raise AssertionError(f"Expected {expected}, got {languages}")
        
        return {"detected_languages": list(languages)}
    
    def test_dockerfile_generation(self):
        """Test Dockerfile generation from analysis"""
        if not MODULES_AVAILABLE:
            raise ImportError("Required modules not available")
        
        dockerfile = generate_dockerfile_from_analysis(
            self.sample_analysis, 
            self.sample_analysis["config_files"]
        )
        
        if not dockerfile or not isinstance(dockerfile, str):
            raise AssertionError("Dockerfile generation failed")
        
        # Check for expected content
        expected_keywords = ["FROM", "WORKDIR", "COPY", "RUN", "EXPOSE", "CMD"]
        for keyword in expected_keywords:
            if keyword not in dockerfile:
                raise AssertionError(f"Missing expected keyword '{keyword}' in Dockerfile")
        
        return {"dockerfile_length": len(dockerfile), "contains_keywords": expected_keywords}
    
    def test_analyze_and_generate_tools(self):
        """Test the main analyze_and_generate_tools function"""
        if not MODULES_AVAILABLE:
            raise ImportError("Required modules not available")
        
        result = asyncio.run(analyze_and_generate_tools(
            repo_id="test-repo",
            files=self.sample_files,
            project_name="Test Project",
            description="A test project for MCP generation"
        ))
        
        # Validate result structure
        required_keys = ["success", "repo_id", "analysis", "mcp_tools", "dockerfile"]
        for key in required_keys:
            if key not in result:
                raise AssertionError(f"Missing required key: {key}")
        
        if not result["success"]:
            raise AssertionError("Analysis should succeed")
        
        if not isinstance(result["mcp_tools"], list):
            raise AssertionError("mcp_tools should be a list")
        
        return {
            "tools_generated": len(result["mcp_tools"]),
            "analysis_languages": result["analysis"]["languages"]
        }
    
    def test_analyze_from_structured_data(self):
        """Test the structured data analysis function"""
        if not MODULES_AVAILABLE:
            raise ImportError("Required modules not available")
        
        result = asyncio.run(analyze_from_structured_data(
            repo_id="test-repo",
            project_name="Test Project",
            description="A test project",
            tree_structure=self.sample_tree,
            analysis=self.sample_analysis,
            important_files=["package.json", "server.js"],
            workspace_path="/tmp/test"
        ))
        
        # Validate result structure
        required_keys = ["success", "repo_id", "mcp_tools", "dockerfile", "ai_analysis"]
        for key in required_keys:
            if key not in result:
                raise AssertionError(f"Missing required key: {key}")
        
        if not result["success"]:
            raise AssertionError("Structured analysis should succeed")
        
        return {
            "tools_generated": len(result["mcp_tools"]),
            "ai_analysis_confidence": result["ai_analysis"]["confidence"]
        }
    
    def test_cli_health_check(self):
        """Test CLI health check command"""
        try:
            result = subprocess.run(
                [sys.executable, "main.py", "health-check"],
                capture_output=True,
                text=True,
                cwd=Path(__file__).parent
            )
            
            if result.returncode != 0:
                raise AssertionError(f"Health check failed with return code {result.returncode}")
            
            response = json.loads(result.stdout)
            if not response.get("success"):
                raise AssertionError("Health check should return success=True")
            
            return {"service": response.get("service"), "status": response.get("status")}
            
        except subprocess.CalledProcessError as e:
            raise AssertionError(f"CLI command failed: {e}")
        except json.JSONDecodeError as e:
            raise AssertionError(f"Invalid JSON response: {e}")
    
    def test_cli_analyze_command(self):
        """Test CLI analyze command with sample data"""
        try:
            # Prepare input data
            input_data = {
                "repo_id": "test-repo",
                "files": self.sample_files,
                "project_name": "Test Project",
                "description": "A test project"
            }
            
            # Run the command
            result = subprocess.run(
                [sys.executable, "main.py", "analyze"],
                input=json.dumps(input_data),
                capture_output=True,
                text=True,
                cwd=Path(__file__).parent
            )
            
            if result.returncode != 0:
                raise AssertionError(f"Analyze command failed with return code {result.returncode}")
            
            response = json.loads(result.stdout)
            if not response.get("success"):
                raise AssertionError("Analyze command should return success=True")
            
            return {
                "tools_generated": len(response.get("mcp_tools", [])),
                "repo_id": response.get("repo_id")
            }
            
        except subprocess.CalledProcessError as e:
            raise AssertionError(f"CLI command failed: {e}")
        except json.JSONDecodeError as e:
            raise AssertionError(f"Invalid JSON response: {e}")
    
    def test_agent_initialization(self):
        """Test IntelligentMCPAgent initialization"""
        if not MODULES_AVAILABLE:
            raise ImportError("Required modules not available")
        
        # Test without API key (should raise error)
        try:
            agent = IntelligentMCPAgent(api_key=None)
            raise AssertionError("Should raise ValueError for missing API key")
        except ValueError:
            pass  # Expected
        
        # Test with dummy API key (should initialize)
        try:
            agent = IntelligentMCPAgent(api_key="test-key")
            return {"agent_initialized": True, "model": agent.model}
        except Exception as e:
            raise AssertionError(f"Agent initialization failed: {e}")
    
    def test_mcp_tool_structure(self):
        """Test that generated MCP tools have correct structure"""
        if not MODULES_AVAILABLE:
            raise ImportError("Required modules not available")
        
        result = asyncio.run(analyze_and_generate_tools(
            repo_id="test-repo",
            files=self.sample_files
        ))
        
        tools = result["mcp_tools"]
        if not tools:
            raise AssertionError("Should generate at least one MCP tool")
        
        # Check tool structure
        required_tool_keys = ["name", "title", "description", "input_schema", "purpose", "implementation_hint"]
        for tool in tools:
            for key in required_tool_keys:
                if key not in tool:
                    raise AssertionError(f"Tool missing required key: {key}")
            
            if not isinstance(tool["name"], str) or not tool["name"]:
                raise AssertionError("Tool name should be a non-empty string")
            
            if not isinstance(tool["input_schema"], dict):
                raise AssertionError("Tool input_schema should be a dict")
        
        return {
            "tools_count": len(tools),
            "tool_names": [tool["name"] for tool in tools]
        }
    
    def run_all_tests(self):
        """Run all tests and return summary"""
        print("🚀 Starting MCP Generation Tests")
        print("=" * 50)
        
        self.setup_test_environment()
        
        try:
            # Define all tests
            tests = [
                ("Language Detection", self.test_language_detection),
                ("Dockerfile Generation", self.test_dockerfile_generation),
                ("Analyze and Generate Tools", self.test_analyze_and_generate_tools),
                ("Structured Data Analysis", self.test_analyze_from_structured_data),
                ("CLI Health Check", self.test_cli_health_check),
                ("CLI Analyze Command", self.test_cli_analyze_command),
                ("Agent Initialization", self.test_agent_initialization),
                ("MCP Tool Structure", self.test_mcp_tool_structure),
            ]
            
            # Run tests
            passed = 0
            total = len(tests)
            
            for test_name, test_func in tests:
                if self.run_test(test_name, test_func):
                    passed += 1
            
            # Print summary
            print("\n" + "=" * 50)
            print("📊 TEST SUMMARY")
            print("=" * 50)
            print(f"Total Tests: {total}")
            print(f"Passed: {passed}")
            print(f"Failed: {total - passed}")
            print(f"Success Rate: {(passed/total)*100:.1f}%")
            
            if passed == total:
                print("🎉 All tests passed!")
            else:
                print("⚠️  Some tests failed. Check the output above for details.")
            
            return {
                "total": total,
                "passed": passed,
                "failed": total - passed,
                "success_rate": (passed/total)*100,
                "results": self.test_results
            }
            
        finally:
            self.cleanup_test_environment()


def main():
    """Main entry point for the test script"""
    print("MCP Generation Test Suite")
    print("Testing LLM module and MCP server logic")
    print()
    
    # Check if we're in the right directory
    if not Path("main.py").exists() or not Path("agent.py").exists():
        print("❌ Error: main.py and agent.py not found in current directory")
        print("Please run this script from the llm/ directory")
        sys.exit(1)
    
    # Run tests
    runner = MCPTestRunner()
    summary = runner.run_all_tests()
    
    # Exit with appropriate code
    if summary["failed"] > 0:
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()
