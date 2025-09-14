# LLM MCP Generation Testing

This directory contains scripts to test the LLM module and MCP server generation logic.

## Quick Start

### 1. Activate Virtual Environment
```bash
source .venv/bin/activate
```

### 2. Run Simple Test
```bash
python3 simple_test.py
```

### 3. Run Full Test Suite
```bash
./run_tests.sh
```

## Test Scripts

### `simple_test.py`
- **Purpose**: Quick test of core functionality
- **What it tests**:
  - Basic language detection
  - Dockerfile generation
  - MCP tool generation (fallback mode)
  - Agent initialization with your .env configuration
  - Intelligent analysis using Groq API
- **Usage**: `python3 simple_test.py`

### `test_mcp_generation.py`
- **Purpose**: Comprehensive test suite
- **What it tests**:
  - All main.py functions
  - CLI interface
  - Agent functionality
  - MCP tool structure validation
- **Usage**: `python3 test_mcp_generation.py`

### `run_tests.sh`
- **Purpose**: Automated test runner with environment setup
- **Features**:
  - Dependency checking and installation
  - Environment validation
  - Multiple test modes
  - Colored output
- **Usage**: 
  - `./run_tests.sh` - Run all tests
  - `./run_tests.sh main` - Run only main.py tests
  - `./run_tests.sh agent` - Run only agent.py tests
  - `./run_tests.sh --setup` - Only setup environment
  - `./run_tests.sh --check` - Only run health check

### Pytest Tests
- **`test_main.py`**: Unit tests for main.py functions
- **`test_agent.py`**: Unit tests for agent.py functions
- **Usage**: `pytest test_main.py test_agent.py -v`

## Environment Configuration

The system now uses hardcoded environment variables:
- **OPENAI_API_KEY**: `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`
- **OPENAI_BASE_URL**: `https://api.groq.com/openai/v1`
- **OPENAI_MODEL**: `openai/gpt-oss-120b`

## Sample Data

### `sample_test_data.json`
Contains comprehensive test data including:
- Sample Express.js API project
- Expected MCP tools
- Test scenarios
- Repository analysis data

## Test Results

### Expected Output from `simple_test.py`:
```
🚀 LLM MCP Generation Test
========================================
🔧 Environment:
   API Key: ✅ Set
   Base URL: https://api.groq.com/openai/v1
   Model: llama-3.1-8b-instant

Basic Functionality:
✅ Detected languages: ['JavaScript']
✅ Generated Dockerfile (125 chars)
✅ Basic Functionality PASSED

MCP Generation:
✅ Generated 1 MCP tools
   - basic-analysis: Basic Project Analysis
✅ MCP Generation PASSED

Agent Initialization:
✅ Agent initialized with model: llama-3.1-8b-instant
✅ Base URL: https://api.groq.com/openai/v1
✅ Agent Initialization PASSED

Agent Analysis:
✅ Selected 14 important files
✅ Analyzed codebase: REST API pattern
✅ Generated 8 intelligent MCP tools
✅ Agent Analysis PASSED

📊 Results: 4/4 tests passed
🎉 All tests passed!
```

## CLI Testing

### Health Check
```bash
python3 main.py health-check
# Expected: {"success": true, "service": "llm-agent", "status": "healthy", "version": "0.1.0"}
```

### Analyze Command
```bash
echo '{"repo_id": "test", "files": {"package.json": "{\"name\": \"test\"}"}}' | python3 main.py analyze
# Expected: JSON with success=true and mcp_tools array
```

### Agent Commands
```bash
# File selection
echo '{"tree_structure": "project/\n├── file.js", "analysis": {"languages": ["JavaScript"]}}' | python3 agent.py select-files

# Dockerfile generation
echo '{"files": {"package.json": "{\"name\": \"test\"}"}, "file_structure": {"languages": ["JavaScript"]}}' | python3 agent.py generate-dockerfile

# Full analysis
echo '{"repo_id": "test", "tree_structure": "...", "analysis": {...}, "important_files": [...]}' | python3 agent.py analyze-and-generate
```

## Troubleshooting

### Common Issues

1. **Module not found errors**
   ```bash
   source .venv/bin/activate
   uv pip install -r requirements.txt
   ```

2. **API key not set**
   - Check your `.env` file has `OPENAI_API_KEY=your_key_here`
   - Verify the key is valid for Groq API

3. **Dependencies missing**
   ```bash
   ./run_tests.sh --install
   ```

4. **Permission denied on scripts**
   ```bash
   chmod +x run_tests.sh
   ```

### Debug Mode

Run tests with verbose output:
```bash
python3 simple_test.py 2>&1 | tee test_output.log
```

## Integration with Main Project

The LLM module is designed to be called from the main Rust application:

1. **Rust calls Python** with repository data
2. **Python analyzes** using Groq API
3. **Python returns** MCP tools and Dockerfile
4. **Rust integrates** results into the system

The test scripts validate this entire pipeline works correctly with your existing configuration.
