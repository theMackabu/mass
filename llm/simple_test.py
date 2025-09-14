#!/usr/bin/env python3
"""
Simple test script for LLM MCP generation
Uses the existing .env file and tests the core functionality
"""

import asyncio
import json
import sys
import os
from pathlib import Path

# Add the current directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

# Hardcoded environment variables
OPENAI_API_KEY = "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"
OPENAI_BASE_URL = "https://api.groq.com/openai/v1"
OPENAI_MODEL = "openai/gpt-oss-120b"

# Import the modules
from main import (
    analyze_and_generate_tools,
    detect_languages_from_files,
    generate_dockerfile_from_analysis
)

try:
    from agent import IntelligentMCPAgent
    AGENT_AVAILABLE = True
except ImportError:
    AGENT_AVAILABLE = False
    print("Warning: agent.py not available")


def test_basic_functionality():
    """Test basic functionality without OpenAI"""
    print("🧪 Testing basic functionality...")
    
    # Test language detection
    sample_files = {
        "app.js": "console.log('hello');",
        "package.json": '{"name": "test"}',
        "README.md": "# Test Project"
    }
    
    languages = detect_languages_from_files(sample_files)
    print(f"✅ Detected languages: {list(languages)}")
    
    # Test Dockerfile generation
    analysis = {
        "languages": ["JavaScript"],
        "config_files": ["package.json"]
    }
    
    dockerfile = generate_dockerfile_from_analysis(analysis, ["package.json"])
    print(f"✅ Generated Dockerfile ({len(dockerfile)} chars)")
    
    return True


async def test_mcp_generation():
    """Test MCP tool generation"""
    print("🧪 Testing MCP tool generation...")
    
    sample_files = {
        "package.json": json.dumps({
            "name": "test-api",
            "scripts": {"start": "node server.js"}
        }),
        "server.js": """
const express = require('express');
const app = express();

app.get('/api/users', (req, res) => {
    res.json([{id: 1, name: 'John'}]);
});

app.post('/api/users', (req, res) => {
    res.status(201).json({id: 2, name: 'Jane'});
});

app.listen(3000);
"""
    }
    
    result = await analyze_and_generate_tools(
        repo_id="test-repo",
        files=sample_files,
        project_name="Test API"
    )
    
    if result["success"]:
        print(f"✅ Generated {len(result['mcp_tools'])} MCP tools")
        for tool in result["mcp_tools"][:3]:  # Show first 3 tools
            print(f"   - {tool['name']}: {tool['title']}")
        return True
    else:
        print("❌ MCP generation failed")
        return False


def test_agent_initialization():
    """Test agent initialization with existing .env"""
    if not AGENT_AVAILABLE:
        print("⚠️  Agent not available, skipping agent tests")
        return True
    
    print("🧪 Testing agent initialization...")
    
    try:
        agent = IntelligentMCPAgent()
        print(f"✅ Agent initialized with model: {agent.model}")
        print(f"✅ Base URL: {agent.base_url}")
        return True
    except Exception as e:
        print(f"❌ Agent initialization failed: {e}")
        return False


async def test_agent_analysis():
    """Test agent analysis with sample data"""
    if not AGENT_AVAILABLE:
        print("⚠️  Agent not available, skipping agent analysis")
        return True
    
    print("🧪 Testing agent analysis...")
    
    try:
        agent = IntelligentMCPAgent()
        
        # Sample data
        tree_structure = """
project/
├── package.json
├── server.js
└── README.md
"""
        
        analysis = {
            "languages": ["JavaScript"],
            "config_files": ["package.json"],
            "file_count": 3
        }
        
        important_files = [
            "package.json:{\"name\": \"test\", \"scripts\": {\"start\": \"node server.js\"}}",
            "server.js:const express = require('express');"
        ]
        
        # Test file selection
        selected_files = await agent.select_important_files(tree_structure, analysis)
        print(f"✅ Selected {len(selected_files)} important files")
        
        # Test codebase analysis
        codebase_analysis = await agent.analyze_codebase_context(
            tree_structure, analysis, important_files
        )
        print(f"✅ Analyzed codebase: {codebase_analysis.get('architecture_pattern', 'Unknown')} pattern")
        
        # Test MCP tools generation
        mcp_tools = await agent.generate_mcp_tools(
            codebase_analysis,
            {"project_name": "Test Project", "repo_id": "test-repo"}
        )
        print(f"✅ Generated {len(mcp_tools)} intelligent MCP tools")
        
        return True
        
    except Exception as e:
        print(f"❌ Agent analysis failed: {e}")
        return False


async def main():
    """Run all tests"""
    print("🚀 LLM MCP Generation Test")
    print("=" * 40)
    
    # Check environment
    api_key = OPENAI_API_KEY
    base_url = OPENAI_BASE_URL
    model = OPENAI_MODEL
    
    print(f"🔧 Environment:")
    print(f"   API Key: {'✅ Set' if api_key else '❌ Not set'}")
    print(f"   Base URL: {base_url or 'Default'}")
    print(f"   Model: {model or 'Default'}")
    print()
    
    tests = [
        ("Basic Functionality", test_basic_functionality),
        ("MCP Generation", test_mcp_generation),
        ("Agent Initialization", test_agent_initialization),
        ("Agent Analysis", test_agent_analysis),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n{test_name}:")
        try:
            if asyncio.iscoroutinefunction(test_func):
                result = await test_func()
            else:
                result = test_func()
            
            if result:
                passed += 1
                print(f"✅ {test_name} PASSED")
            else:
                print(f"❌ {test_name} FAILED")
        except Exception as e:
            print(f"❌ {test_name} FAILED: {e}")
    
    print("\n" + "=" * 40)
    print(f"📊 Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed!")
        return 0
    else:
        print("⚠️  Some tests failed")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
