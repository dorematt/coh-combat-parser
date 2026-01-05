#!/bin/bash

# City of Heroes Combat Parser - Local Development Runner
# This script sets up a virtual environment and runs the parser

set -e  # Exit on error

VENV_DIR="venv"
PYTHON_CMD="python3"

echo "================================================="
echo "  CoH Combat Parser - Local Development Runner  "
echo "================================================="
echo ""

# Check if Python is installed
if ! command -v $PYTHON_CMD &> /dev/null; then
    echo "ERROR: Python 3 is not installed or not in PATH"
    echo "Please install Python 3.12 or later from https://www.python.org/"
    exit 1
fi

# Display Python version
PYTHON_VERSION=$($PYTHON_CMD --version)
echo "Using: $PYTHON_VERSION"
echo ""

# Create virtual environment if it doesn't exist
if [ ! -d "$VENV_DIR" ]; then
    echo "Creating virtual environment..."
    $PYTHON_CMD -m venv $VENV_DIR
    echo "Virtual environment created successfully!"
    echo ""
fi

# Activate virtual environment
echo "Activating virtual environment..."
source $VENV_DIR/bin/activate

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip -q

# Install/update dependencies
echo "Installing dependencies from requirements.txt..."
pip install -r requirements.txt -q

echo ""
echo "================================================="
echo "  Starting CoH Combat Parser..."
echo "================================================="
echo ""

# Run the application
cd src
python CoH_Parser.py

# Deactivate on exit
deactivate
