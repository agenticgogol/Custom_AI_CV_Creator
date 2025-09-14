#!/bin/bash

MODE=${1:-dev}

echo "Starting Enhanced CV Creator Agent..."

# Load environment variables if .env file exists
if [ -f ".env" ]; then
    echo "Loading environment variables from .env file..."
    export $(grep -v '^#' .env | xargs)
fi

# NOTE: API keys are now configured through the UI, so they're no longer required at startup
# The application will prompt users to configure their preferred LLM provider and API key

# Check for optional environment variables (no longer required)
if [ -z "$FIREWORKS_API_KEY" ] && [ -z "$OPENAI_API_KEY" ] && [ -z "$GOOGLE_API_KEY" ]; then
    echo "ℹ️  No API keys found in environment variables."
    echo "   Users will configure their preferred AI provider (OpenAI or Gemini) through the web interface."
    echo "   This is the recommended approach for security and flexibility."
fi

# Set default values for optional variables
export HOST=${HOST:-0.0.0.0}
export PORT=${PORT:-8080}

if [ "$MODE" = "prod" ]; then
    echo "Starting Enhanced CV Creator Agent in production mode..."
    echo "🤖 Multi-LLM Support: OpenAI GPT-4, Google Gemini"
    echo "🔧 User Configuration: API keys configured via web interface"
    export ENVIRONMENT=production
    python -m cv_agent.main
elif [ "$MODE" = "dev" ]; then
    echo "Starting Enhanced CV Creator Agent in development mode..."
    echo "🤖 Multi-LLM Support: OpenAI GPT-4, Google Gemini"
    echo "🔧 User Configuration: API keys configured via web interface"
    echo "🌐 Access the app at: http://localhost:${PORT}"
    export ENVIRONMENT=development
    python -m cv_agent.main
elif [ "$MODE" = "test" ]; then
    echo "Running tests..."
    # Check if pytest is installed
    if ! command -v pytest &> /dev/null; then
        echo "Installing pytest..."
        pip install pytest pytest-asyncio
    fi
    python -m pytest tests/ -v
else
    echo "Invalid mode. Usage: $0 [dev|prod|test]"
    echo ""
    echo "Modes:"
    echo "  dev   - Development mode with enhanced features"
    echo "  prod  - Production mode"
    echo "  test  - Run tests"
    echo ""
    echo "Enhanced Features:"
    echo "  📊 ATS Compliance Scoring"
    echo "  🔍 Comprehensive Gap Analysis" 
    echo "  📝 Change Tracking & Highlighting"
    echo "  💬 User Feedback Integration"
    echo "  📄 Multiple Export Formats (PDF, DOCX, TXT)"
    echo "  🤖 Multi-LLM Support (OpenAI, Gemini)"
    echo "  🔧 Dynamic API Configuration"
    echo ""
    echo "Example: $0 dev"
    exit 1
fi