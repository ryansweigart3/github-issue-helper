#!/bin/bash

# Tissue Installation Script
# This script ensures a clean installation without package conflicts

set -e  # Exit on any error

echo "🩹 Tissue Installation Script"
echo "================================"

# Check if Python 3 is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is required but not found"
    exit 1
fi

echo "✅ Python 3 found: $(python3 --version)"

# Create virtual environment
echo "📦 Creating virtual environment..."
if [ -d "venv" ]; then
    echo "⚠️  Removing existing venv directory"
    rm -rf venv
fi

python3 -m venv venv

# Activate virtual environment
echo "🔄 Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "⬆️  Upgrading pip..."
pip install --upgrade pip

# Remove any conflicting packages
echo "🧹 Removing any conflicting 'github' packages..."
pip uninstall -y github 2>/dev/null || true
pip uninstall -y PyGithub 2>/dev/null || true

# Install core dependencies explicitly
echo "📦 Installing core dependencies..."
pip install "PyGithub>=1.58.0"
pip install "click>=8.0.0"
pip install "pandas>=1.5.0"

# Install development dependencies
echo "🔧 Installing development dependencies..."
pip install "pytest>=7.0.0"
pip install "pytest-cov>=4.0.0"

# Install the package in development mode
echo "🔨 Installing Tissue in development mode..."
pip install -e .

# Force reinstall to ensure console scripts are updated
echo "🔄 Updating console scripts..."
pip install --force-reinstall --no-deps -e .

# Verify installation
echo "✅ Verifying installation..."
python -c "
try:
    from github import Github, GithubException
    print('✅ PyGithub imported successfully')
    
    from src.csv_parser import CSVParser
    print('✅ CSV Parser imported successfully')
    
    from src.github_client import GitHubClient
    print('✅ GitHub Client imported successfully')
    
    print('✅ All core modules imported successfully')
    
except ImportError as e:
    print(f'❌ Import failed: {e}')
    exit(1)
"

# Test CLI command
echo "🧪 Testing CLI command..."
if python -m src.main --help > /dev/null 2>&1; then
    echo "✅ CLI module works!"
elif tissue --help > /dev/null 2>&1; then
    echo "✅ tissue command works!"
else 
    echo "⚠️  tissue command not in PATH, but module works"
    echo "   You can run: python -m src.main --help"
fi

echo ""
echo "🎉 Installation completed successfully!"
echo ""
echo "To activate the environment in the future, run:"
echo "  source venv/bin/activate"
echo ""
echo "To use tissue, try either:"
echo "  tissue --help                # If tissue command is in PATH"
echo "  python -m src.main --help    # Alternative method"
echo ""
echo "Example usage:"
echo "  tissue --file issues.csv --repo owner/repo --token ghp_xxx"

