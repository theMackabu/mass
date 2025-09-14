#!/bin/bash
# Test runner script for LLM MCP generation

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to check if we're in the right directory
check_directory() {
    if [[ ! -f "main.py" ]] || [[ ! -f "agent.py" ]]; then
        print_error "main.py and agent.py not found in current directory"
        print_error "Please run this script from the llm/ directory"
        exit 1
    fi
}

# Function to check Python environment
check_python_env() {
    print_status "Checking Python environment..."
    
    if ! command_exists python3; then
        print_error "Python 3 is not installed"
        exit 1
    fi
    
    python_version=$(python3 --version 2>&1 | cut -d' ' -f2)
    print_status "Python version: $python_version"
    
    # Check if we're in a virtual environment
    if [[ -n "$VIRTUAL_ENV" ]]; then
        print_success "Virtual environment detected: $VIRTUAL_ENV"
    else
        print_warning "No virtual environment detected"
        print_warning "Consider using 'uv venv' to create a virtual environment"
    fi
}

# Function to check dependencies
check_dependencies() {
    print_status "Checking dependencies..."
    
    # Check if uv is available
    if command_exists uv; then
        print_success "uv is available"
        USE_UV=true
    else
        print_warning "uv not found, falling back to pip"
        USE_UV=false
    fi
    
    # Check if pytest is available
    if command_exists pytest; then
        print_success "pytest is available"
    else
        print_warning "pytest not found, will install it"
        if [[ "$USE_UV" == true ]]; then
            uv pip install pytest pytest-asyncio
        else
            pip install pytest pytest-asyncio
        fi
    fi
}

# Function to install dependencies
install_dependencies() {
    print_status "Installing dependencies..."
    
    if [[ "$USE_UV" == true ]]; then
        print_status "Using uv to install dependencies..."
        uv pip install -e .
        uv pip install pytest pytest-asyncio
    else
        print_status "Using pip to install dependencies..."
        pip install -e .
        pip install pytest pytest-asyncio
    fi
    
    print_success "Dependencies installed"
}

# Function to check environment variables
check_env_vars() {
    print_status "Checking environment variables..."
    
    if [[ -f ".env" ]]; then
        print_success ".env file found"
        source .env
    elif [[ -f ".env.example" ]]; then
        print_warning ".env file not found, but .env.example exists"
        print_warning "Copy .env.example to .env and configure your API keys"
    else
        print_warning "No .env file found"
    fi
    
    if [[ -n "$OPENAI_API_KEY" ]]; then
        print_success "OPENAI_API_KEY is set"
    else
        print_warning "OPENAI_API_KEY is not set"
        print_warning "Some tests may fail without a valid API key"
    fi
}

# Function to run the main test script
run_main_tests() {
    print_status "Running main test script..."
    
    if [[ -f "test_mcp_generation.py" ]]; then
        python3 test_mcp_generation.py
        if [[ $? -eq 0 ]]; then
            print_success "Main test script passed"
        else
            print_error "Main test script failed"
            return 1
        fi
    else
        print_error "test_mcp_generation.py not found"
        return 1
    fi
}

# Function to run pytest tests
run_pytest_tests() {
    print_status "Running pytest tests..."
    
    # Run tests with verbose output
    if command_exists pytest; then
        pytest test_main.py test_agent.py -v --tb=short
        if [[ $? -eq 0 ]]; then
            print_success "Pytest tests passed"
        else
            print_error "Pytest tests failed"
            return 1
        fi
    else
        print_error "pytest not available"
        return 1
    fi
}

# Function to run specific test categories
run_specific_tests() {
    local test_type="$1"
    
    case "$test_type" in
        "main")
            print_status "Running main.py tests only..."
            pytest test_main.py -v --tb=short
            ;;
        "agent")
            print_status "Running agent.py tests only..."
            pytest test_agent.py -v --tb=short
            ;;
        "integration")
            print_status "Running integration tests..."
            python3 test_mcp_generation.py
            ;;
        *)
            print_error "Unknown test type: $test_type"
            print_error "Available types: main, agent, integration"
            return 1
            ;;
    esac
}

# Function to run health check
run_health_check() {
    print_status "Running health check..."
    
    python3 main.py health-check
    if [[ $? -eq 0 ]]; then
        print_success "Health check passed"
    else
        print_error "Health check failed"
        return 1
    fi
}

# Function to show help
show_help() {
    echo "Usage: $0 [OPTIONS] [TEST_TYPE]"
    echo ""
    echo "Options:"
    echo "  -h, --help     Show this help message"
    echo "  -s, --setup    Only run setup (check dependencies, install, etc.)"
    echo "  -c, --check    Only run health check"
    echo "  -i, --install  Only install dependencies"
    echo ""
    echo "Test Types:"
    echo "  main          Run only main.py tests"
    echo "  agent         Run only agent.py tests"
    echo "  integration   Run only integration tests"
    echo "  all           Run all tests (default)"
    echo ""
    echo "Examples:"
    echo "  $0                    # Run all tests"
    echo "  $0 main               # Run only main.py tests"
    echo "  $0 --setup            # Only setup environment"
    echo "  $0 --check            # Only run health check"
}

# Main function
main() {
    local test_type="all"
    local setup_only=false
    local check_only=false
    local install_only=false
    
    # Parse command line arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            -h|--help)
                show_help
                exit 0
                ;;
            -s|--setup)
                setup_only=true
                shift
                ;;
            -c|--check)
                check_only=true
                shift
                ;;
            -i|--install)
                install_only=true
                shift
                ;;
            main|agent|integration|all)
                test_type="$1"
                shift
                ;;
            *)
                print_error "Unknown option: $1"
                show_help
                exit 1
                ;;
        esac
    done
    
    print_status "Starting LLM MCP Test Suite"
    print_status "=============================="
    
    # Check directory
    check_directory
    
    # Check Python environment
    check_python_env
    
    # Check dependencies
    check_dependencies
    
    # Install dependencies if needed
    if [[ "$install_only" == true ]]; then
        install_dependencies
        exit 0
    fi
    
    # Check environment variables
    check_env_vars
    
    if [[ "$setup_only" == true ]]; then
        print_success "Setup completed"
        exit 0
    fi
    
    if [[ "$check_only" == true ]]; then
        run_health_check
        exit $?
    fi
    
    # Run tests based on type
    local exit_code=0
    
    case "$test_type" in
        "all")
            print_status "Running all tests..."
            
            # Run health check first
            if ! run_health_check; then
                exit_code=1
            fi
            
            # Run main test script
            if ! run_main_tests; then
                exit_code=1
            fi
            
            # Run pytest tests
            if ! run_pytest_tests; then
                exit_code=1
            fi
            ;;
        *)
            if ! run_specific_tests "$test_type"; then
                exit_code=1
            fi
            ;;
    esac
    
    # Print final results
    echo ""
    print_status "Test Suite Complete"
    print_status "==================="
    
    if [[ $exit_code -eq 0 ]]; then
        print_success "All tests passed! 🎉"
    else
        print_error "Some tests failed! ❌"
    fi
    
    exit $exit_code
}

# Run main function with all arguments
main "$@"
