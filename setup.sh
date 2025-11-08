#!/bin/bash

# FiveM Webhook Manager - Quick Setup Script

echo "=========================================="
echo "FiveM Webhook Manager v6.0 - Setup"
echo "=========================================="
echo ""

# Check Python version
echo "Checking Python version..."
python_version=$(python3 --version 2>&1)
if [ $? -eq 0 ]; then
    echo "✓ Found: $python_version"
else
    echo "✗ Python 3 not found. Please install Python 3.7 or higher."
    exit 1
fi

echo ""

# Install dependencies
echo "Installing dependencies..."
pip3 install -r requirements.txt

if [ $? -eq 0 ]; then
    echo "✓ Dependencies installed successfully"
else
    echo "✗ Failed to install dependencies"
    exit 1
fi

echo ""

# Create .env if not exists
if [ ! -f .env ]; then
    echo "Creating .env file..."
    cp .env.example .env
    echo "✓ Created .env file"
    echo ""
    echo "⚠️  IMPORTANT: Edit .env and add your:"
    echo "   - Discord Bot Token"
    echo "   - Discord Guild ID"
    echo "   - FiveM Resources Path"
    echo ""
else
    echo "✓ .env file already exists"
fi

echo ""
echo "=========================================="
echo "Setup Complete!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "1. Edit .env with your configuration"
echo "2. Run in dry-run mode first:"
echo "   python3 fivem_webhook_manager.py"
echo "3. Review the output"
echo "4. Set DRY_RUN=false in .env"
echo "5. Run for real!"
echo ""
echo "For help, check README.md"
echo ""
