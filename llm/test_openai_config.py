#!/usr/bin/env python3
"""
Test OpenAI configuration with custom base URLs
"""

import asyncio
import os
import json

# Test without importing the full agent
async def test_openai_config():
    try:
        import openai
        from openai import AsyncOpenAI
        
        # Test different configuration scenarios
        configs = [
            {
                "name": "Default OpenAI",
                "api_key": os.getenv('OPENAI_API_KEY'),
                "base_url": None
            },
            {
                "name": "Custom Base URL",
                "api_key": os.getenv('OPENAI_API_KEY') or 'test-key',
                "base_url": os.getenv('OPENAI_BASE_URL')
            },
            {
                "name": "Local Model (Example)",
                "api_key": "not-needed-for-local",
                "base_url": "http://localhost:11434/v1"  # Ollama example
            }
        ]
        
        for config in configs:
            print(f"\n🧪 Testing: {config['name']}")
            
            try:
                client_kwargs = {"api_key": config["api_key"] or "test-key"}
                if config["base_url"]:
                    client_kwargs["base_url"] = config["base_url"]
                    
                client = AsyncOpenAI(**client_kwargs)
                
                print(f"✅ Client initialized successfully")
                print(f"   API Key: {'***' + config['api_key'][-8:] if config['api_key'] and len(config['api_key']) > 8 else 'None'}")
                print(f"   Base URL: {config['base_url'] or 'Default (https://api.openai.com/v1)'}")
                
                # Note: Not making actual API calls to avoid costs/errors
                print(f"   Status: Ready for API calls")
                
            except Exception as e:
                print(f"❌ Failed to initialize: {e}")
        
        return {
            "success": True,
            "openai_available": True,
            "configs_tested": len(configs)
        }
        
    except ImportError as e:
        return {
            "success": False,
            "openai_available": False,
            "error": f"OpenAI library not available: {e}"
        }

if __name__ == "__main__":
    result = asyncio.run(test_openai_config())
    print(f"\n📊 Test Results:")
    print(json.dumps(result, indent=2))