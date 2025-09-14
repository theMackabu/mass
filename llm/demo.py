#!/usr/bin/env python3
"""
Demo script showing MCP generation in action
"""

import asyncio
import json
import sys
from pathlib import Path

# Add the current directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

# Hardcoded environment variables
OPENAI_API_KEY = "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"
OPENAI_BASE_URL = "https://api.groq.com/openai/v1"
OPENAI_MODEL = "openai/gpt-oss-120b"

from agent import IntelligentMCPAgent


async def demo_mcp_generation():
    """Demo the MCP generation process"""
    print("🚀 MCP Generation Demo")
    print("=" * 50)
    
    # Sample project data (like what would come from Rust)
    sample_data = {
        "repo_id": "demo-express-api",
        "project_name": "Express.js User Management API",
        "description": "A RESTful API for user management with MongoDB",
        "tree_structure": """
express-user-api/
├── package.json
├── server.js
├── models/
│   └── User.js
├── routes/
│   └── users.js
├── tests/
│   └── user.test.js
├── Dockerfile
└── README.md
""",
        "analysis": {
            "languages": ["JavaScript", "JSON"],
            "config_files": ["package.json", "Dockerfile"],
            "file_count": 7,
            "size_bytes": 15420,
            "frameworks": ["Express.js", "Mongoose"],
            "hasPackageJson": True,
            "hasDockerfile": True,
            "hasTests": True
        },
        "important_files": [
            "package.json:{\"name\": \"express-user-api\", \"version\": \"1.0.0\", \"scripts\": {\"start\": \"node server.js\", \"test\": \"jest\"}, \"dependencies\": {\"express\": \"^4.18.2\", \"mongoose\": \"^7.5.0\"}}",
            "server.js:const express = require('express');\nconst mongoose = require('mongoose');\nconst userRoutes = require('./routes/users');\n\nconst app = express();\napp.use(express.json());\napp.use('/api/users', userRoutes);\n\nmongoose.connect(process.env.MONGODB_URI);\napp.listen(3000, () => console.log('Server running on port 3000'));",
            "routes/users.js:const express = require('express');\nconst User = require('../models/User');\nconst router = express.Router();\n\nrouter.get('/', async (req, res) => {\n  try {\n    const users = await User.find();\n    res.json(users);\n  } catch (error) {\n    res.status(500).json({ error: error.message });\n  }\n});\n\nrouter.post('/', async (req, res) => {\n  try {\n    const user = new User(req.body);\n    await user.save();\n    res.status(201).json(user);\n  } catch (error) {\n    res.status(400).json({ error: error.message });\n  }\n});\n\nmodule.exports = router;",
            "models/User.js:const mongoose = require('mongoose');\n\nconst userSchema = new mongoose.Schema({\n  name: { type: String, required: true },\n  email: { type: String, required: true, unique: true },\n  age: { type: Number, min: 0 }\n}, { timestamps: true });\n\nmodule.exports = mongoose.model('User', userSchema);"
        ]
    }
    
    try:
        # Initialize agent
        print("🔧 Initializing intelligent agent...")
        agent = IntelligentMCPAgent()
        print(f"   Model: {agent.model}")
        print(f"   Base URL: {agent.base_url}")
        print()
        
        # Step 1: File selection (already done in this demo)
        print("📁 Step 1: Important files selected")
        print(f"   Selected {len(sample_data['important_files'])} key files for analysis")
        print()
        
        # Step 2: Codebase analysis
        print("🔍 Step 2: Analyzing codebase...")
        codebase_analysis = await agent.analyze_codebase_context(
            sample_data["tree_structure"],
            sample_data["analysis"],
            sample_data["important_files"]
        )
        
        print(f"   Architecture: {codebase_analysis.get('architecture_pattern', 'Unknown')}")
        print(f"   API Endpoints: {len(codebase_analysis.get('api_endpoints', []))}")
        print(f"   Key Functions: {len(codebase_analysis.get('key_functions', []))}")
        print(f"   Technologies: {', '.join(codebase_analysis.get('main_technologies', []))}")
        print()
        
        # Step 3: Generate MCP tools
        print("🛠️  Step 3: Generating MCP tools...")
        mcp_tools = await agent.generate_mcp_tools(
            codebase_analysis,
            {
                "project_name": sample_data["project_name"],
                "repo_id": sample_data["repo_id"]
            }
        )
        
        print(f"   Generated {len(mcp_tools)} MCP tools:")
        for i, tool in enumerate(mcp_tools, 1):
            print(f"   {i}. {tool['name']} - {tool['title']}")
            print(f"      {tool['description']}")
            print(f"      Category: {tool.get('category', 'N/A')}")
            print()
        
        # Step 4: Generate documentation
        print("📚 Step 4: Generating documentation...")
        documentation = await agent.generate_documentation_resource(
            codebase_analysis,
            mcp_tools,
            {
                "project_name": sample_data["project_name"],
                "repo_id": sample_data["repo_id"]
            }
        )
        
        print(f"   Generated {len(documentation)} characters of documentation")
        print("   Preview:")
        print("   " + documentation[:200] + "..." if len(documentation) > 200 else "   " + documentation)
        print()
        
        # Step 5: Generate MCP server template (simplified approach)
        print("🏗️  Step 5: Generating MCP server setup...")
        print("   Using simplified approach: Dockerfile + base package.json + server.js")
        print("   This allows running MCP tools directly from the cloned GitHub repo")
        print()
        
        # Step 6: Generate Dockerfile
        print("🐳 Step 6: Generating Dockerfile...")
        dockerfile = await agent.generate_dockerfile_for_repository(
            {f.split(':')[0]: f.split(':', 1)[1] for f in sample_data["important_files"] if ':' in f},
            sample_data["analysis"],
            codebase_analysis.get("api_endpoints", []),
            {
                "project_name": sample_data["project_name"],
                "repo_id": sample_data["repo_id"]
            }
        )
        
        print(f"   Generated {len(dockerfile)} character Dockerfile")
        print("   Preview:")
        print("   " + dockerfile[:200] + "..." if len(dockerfile) > 200 else "   " + dockerfile)
        print()
        
        # Summary
        print("📊 Summary:")
        print(f"   Repository: {sample_data['project_name']}")
        print(f"   Architecture: {codebase_analysis.get('architecture_pattern', 'Unknown')}")
        print(f"   MCP Tools: {len(mcp_tools)}")
        print(f"   Documentation: {len(documentation)} chars")
        print(f"   Dockerfile: {len(dockerfile)} chars")
        print()
        print("🎉 MCP generation completed successfully!")
        print()
        print("💡 Next steps:")
        print("   1. Use the generated Dockerfile to containerize the project")
        print("   2. Create a simple package.json with MCP SDK dependencies")
        print("   3. Create a server.js that loads and exposes the MCP tools")
        print("   4. The MCP tools can then be used to interact with the cloned repo")
        
        return True
        
    except Exception as e:
        print(f"❌ Demo failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(demo_mcp_generation())
    sys.exit(0 if success else 1)
