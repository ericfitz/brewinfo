#!/bin/bash
# Script to set up virtual environment for brewinfo project

echo "Setting up virtual environment for brewinfo project..."

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python -m venv venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install dependencies (using --no-user to avoid pip config conflicts)
echo "Installing dependencies..."
pip install --no-user -r requirements.txt

# Upgrade pip if needed
echo "Upgrading pip..."
pip install --no-user --upgrade pip

echo "Virtual environment setup complete!"
echo "To activate the virtual environment, run: source venv/bin/activate"
echo "To deactivate, run: deactivate"