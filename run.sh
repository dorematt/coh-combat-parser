#!/bin/bash

# City of Heroes Combat Parser - Local Development Runner
# This script sets up a virtual environment and runs the parser

set -e  # Exit on error

VENV_DIR="venv"
PYTHON_CMD=""

echo "================================================="
echo "  CoH Combat Parser - Local Development Runner  "
echo "================================================="
echo ""

# Try to find Python 3.12 in order of preference
echo "Searching for Python 3.12..."

# 1. Try python3.12 command (most explicit)
if command -v python3.12 &> /dev/null; then
    PYTHON_CMD="python3.12"
    echo "Found python3.12"
# 2. Try python312 command
elif command -v python312 &> /dev/null; then
    PYTHON_CMD="python312"
    echo "Found python312"
# 3. Check if default python3 is version 3.12
elif command -v python3 &> /dev/null; then
    PYTHON_CMD="python3"
    echo "Found python3"
# 4. Check if python is version 3.12
elif command -v python &> /dev/null; then
    PYTHON_CMD="python"
    echo "Found python"
else
    echo "ERROR: Python is not installed or not in PATH"
    echo "Please install Python 3.12 from https://www.python.org/"
    exit 1
fi

# Display and check Python version
PYTHON_VERSION=$($PYTHON_CMD --version 2>&1)
echo "Using: $PYTHON_VERSION"

# Extract version numbers (e.g., "Python 3.12.1" -> "3.12")
VERSION_NUMBER=$(echo $PYTHON_VERSION | grep -oP '\d+\.\d+' | head -1)
MAJOR_VERSION=$(echo $VERSION_NUMBER | cut -d. -f1)
MINOR_VERSION=$(echo $VERSION_NUMBER | cut -d. -f2)

# Check if version is 3.12
if [ "$MAJOR_VERSION" != "3" ] || [ "$MINOR_VERSION" != "12" ]; then
    echo ""
    echo "WARNING: Python 3.12 is required for this project."
    echo "You are using Python $VERSION_NUMBER which may not be compatible."
    echo "PyQt5 and other dependencies may fail to install on Python 3.13+."
    echo ""
    echo "Please install Python 3.12 from https://www.python.org/"
    echo ""
    read -p "Continue anyway? (y/N): " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi
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
