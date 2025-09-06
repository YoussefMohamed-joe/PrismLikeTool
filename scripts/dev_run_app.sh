#!/bin/bash
# Development script to run Vogue Manager Desktop Application
# Unix/Linux shell script

echo "Starting Vogue Manager Desktop Application..."

# Change to project root directory
cd "$(dirname "$0")/.."

# Add src to Python path
export PYTHONPATH="$PWD/src:$PYTHONPATH"

# Run the application
python -m vogue_app.main
