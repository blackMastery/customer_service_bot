#!/bin/bash

# Customer Service Chatbot - Quick Setup Script
# This script automates the setup process

set -e  # Exit on error

echo "🤖 Customer Service Chatbot - Setup Script"
echo "=========================================="
echo ""

# Check Python version
echo "✓ Checking Python version..."
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "  Python version: $python_version"

# Check if python version is 3.11+
if ! python3 -c 'import sys; exit(0 if sys.version_info >= (3, 11) else 1)' 2>/dev/null; then
    echo "❌ Error: Python 3.11 or higher is required"
    exit 1
fi

# Create virtual environment
echo ""
echo "✓ Creating virtual environment..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo "  Virtual environment created"
else
    echo "  Virtual environment already exists"
fi

# Activate virtual environment
echo ""
echo "✓ Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo ""
echo "✓ Installing dependencies..."
pip install --upgrade pip > /dev/null 2>&1
pip install -r requirements.txt > /dev/null 2>&1
echo "  Dependencies installed"

# Create .env file if it doesn't exist
echo ""
echo "✓ Setting up environment configuration..."
if [ ! -f ".env" ]; then
    cp .env.example .env
    echo "  Created .env file from template"
    echo "  ⚠️  IMPORTANT: Edit .env file and add your API keys!"
else
    echo "  .env file already exists"
fi

# Create data directories
echo ""
echo "✓ Creating data directories..."
mkdir -p data/knowledge_base
mkdir -p data/vectorstore
mkdir -p logs
echo "  Directories created"

# Build knowledge base
echo ""
echo "✓ Building knowledge base..."
python build_knowledge_base.py build > /dev/null 2>&1
echo "  Knowledge base built with sample documents"

# Run tests
echo ""
echo "✓ Running tests..."
if pytest test_chatbot.py -v --tb=short > /dev/null 2>&1; then
    echo "  All tests passed"
else
    echo "  ⚠️  Some tests failed (this is expected without API keys)"
fi

echo ""
echo "=========================================="
echo "✅ Setup Complete!"
echo ""
echo "Next steps:"
echo "1. Edit .env file with your API keys:"
echo "   nano .env"
echo ""
echo "2. Start the application:"
echo "   Option A - API Server:"
echo "     python main.py"
echo "     API: http://localhost:8000"
echo "     Docs: http://localhost:8000/docs"
echo ""
echo "   Option B - Streamlit UI:"
echo "     streamlit run streamlit_app.py"
echo "     UI: http://localhost:8501"
echo ""
echo "   Option C - Docker (both):"
echo "     docker-compose up -d"
echo ""
echo "3. Add your own documents to data/knowledge_base/"
echo "   and rebuild with:"
echo "     python build_knowledge_base.py build"
echo ""
echo "For more info, see README.md"
echo ""
