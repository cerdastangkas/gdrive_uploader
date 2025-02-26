#!/bin/bash
# Script to add a folder to the to_upload directory

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Change to the script directory
cd "$SCRIPT_DIR" || exit 1

# Check if virtual environment exists, if not create it
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
else
    source venv/bin/activate
fi

# Parse command line arguments
MOVE_FLAG=""
FOLDER_PATH=""

if [ $# -eq 0 ]; then
    echo "Usage: $0 [--move] FOLDER_PATH"
    echo "  FOLDER_PATH: Path to the folder to add"
    echo "  --move: Move the folder instead of copying it"
    exit 1
fi

while [[ $# -gt 0 ]]; do
    case "$1" in
        --move)
            MOVE_FLAG="--move"
            shift
            ;;
        *)
            FOLDER_PATH="$1"
            shift
            ;;
    esac
done

if [ -z "$FOLDER_PATH" ]; then
    echo "Error: No folder path specified."
    echo "Usage: $0 [--move] FOLDER_PATH"
    exit 1
fi

# Run the add folder script
python gdrive_uploader_cli.py add-folder $MOVE_FLAG "$FOLDER_PATH"

# Deactivate virtual environment
deactivate
