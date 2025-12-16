#!/usr/bin/env bash

# EC2 Instance State Control Script - Wrapper for Python implementation
# This script checks for Python and boto3 dependency

set -euo pipefail

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_SCRIPT="$SCRIPT_DIR/statecontrol-ec2.py"

# Function to print colored output
print_color() {
    local color=$1
    shift
    echo -e "${color}$*${NC}"
}

# Check if Python 3 is installed
if ! command -v python3 &> /dev/null; then
    print_color "$RED" "Error: Python 3 is not installed or not in PATH"
    print_color "$YELLOW" "Please install Python 3.6 or later"
    exit 1
fi

# Check Python version
PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
REQUIRED_VERSION="3.6"

if [ "$(printf '%s\n' "$REQUIRED_VERSION" "$PYTHON_VERSION" | sort -V | head -n1)" != "$REQUIRED_VERSION" ]; then
    print_color "$RED" "Error: Python $PYTHON_VERSION is too old"
    print_color "$YELLOW" "Please install Python $REQUIRED_VERSION or later"
    exit 1
fi

# Check if boto3 is installed (required)
if ! python3 -c "import boto3" 2>/dev/null; then
    print_color "$RED" "Error: boto3 Python package is not installed"
    print_color "$YELLOW" "Please install boto3 using one of these methods:"
    print_color "$YELLOW" "  1. System package manager: pacman -S python-boto3"
    print_color "$YELLOW" "  2. Using pipx: pipx install boto3"
    print_color "$YELLOW" "  3. In a virtual environment: python3 -m venv venv && venv/bin/pip install boto3"
    print_color "$YELLOW" "  4. User install (may require --break-system-packages): pip3 install --user boto3"
    exit 1
fi

# Check if the Python script exists
if [ ! -f "$PYTHON_SCRIPT" ]; then
    print_color "$RED" "Error: Python script not found at $PYTHON_SCRIPT"
    exit 1
fi

# Make the Python script executable if it isn't already
if [ ! -x "$PYTHON_SCRIPT" ]; then
    chmod +x "$PYTHON_SCRIPT"
fi

# Run the Python script with all arguments
exec python3 "$PYTHON_SCRIPT" "$@"
