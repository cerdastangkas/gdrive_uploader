#!/bin/bash

# Script to easily upload a folder to Google Drive

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is required but not installed."
    exit 1
fi

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Check if the folder path is provided
if [ $# -lt 1 ]; then
    echo "Usage: $0 /path/to/folder [--parent-id PARENT_ID] [--force]"
    echo "Options:"
    echo "  --parent-id PARENT_ID  Upload to a specific folder in Google Drive"
    echo "  --force                Force upload even if the folder has been uploaded before"
    echo ""
    echo "Example: $0 ~/Documents/MyFolder"
    echo "Example with parent folder: $0 ~/Documents/MyFolder --parent-id 1a2b3c4d5e6f7g8h9i0j"
    echo "Example with force upload: $0 ~/Documents/MyFolder --force"
    exit 1
fi

# Check if virtual environment exists, if not create it
if [ ! -d "$SCRIPT_DIR/venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv "$SCRIPT_DIR/venv"
    
    echo "Installing dependencies..."
    "$SCRIPT_DIR/venv/bin/pip" install -r "$SCRIPT_DIR/requirements.txt"
fi

# Activate virtual environment and run the script
echo "Uploading folder to Google Drive..."
"$SCRIPT_DIR/venv/bin/python" "$SCRIPT_DIR/gdrive_uploader.py" "$@"
