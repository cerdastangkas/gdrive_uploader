#!/bin/bash
# Script to check the status of uploaded folders

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

# Ensure the data directories exist
mkdir -p data/to_upload
mkdir -p data/uploaded

# Display status information
echo "===== Google Drive Uploader Status ====="
echo ""

# Check to_upload directory
TO_UPLOAD_COUNT=$(find data/to_upload -maxdepth 1 -mindepth 1 -type d | wc -l)
if [ "$TO_UPLOAD_COUNT" -eq 0 ]; then
    echo "No folders pending upload in data/to_upload"
else
    echo "$TO_UPLOAD_COUNT folder(s) pending upload in data/to_upload:"
    find data/to_upload -maxdepth 1 -mindepth 1 -type d -exec basename {} \; | sort | sed 's/^/  - /'
fi

echo ""

# Check uploaded directory
UPLOADED_COUNT=$(find data/uploaded -maxdepth 1 -mindepth 1 -type d | wc -l)
if [ "$UPLOADED_COUNT" -eq 0 ]; then
    echo "No folders have been uploaded yet"
else
    echo "$UPLOADED_COUNT folder(s) successfully uploaded (in data/uploaded):"
    find data/uploaded -maxdepth 1 -mindepth 1 -type d -exec basename {} \; | sort | sed 's/^/  - /'
fi

echo ""
echo "To view details of uploaded folders, run:"
echo "  python gdrive_uploader_cli.py manage list"

# Deactivate virtual environment
deactivate
