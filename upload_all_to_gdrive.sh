#!/bin/bash
# Script to upload all folders in the to_upload directory to Google Drive
# Successfully uploaded folders will be moved to the uploaded directory

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

# Parse command line arguments
FORCE_FLAG=""
PARENT_ID=""
TIMEOUT=""
WORKERS="--workers=5"
BATCH_SIZE="--batch-size=100"

while [[ $# -gt 0 ]]; do
    case "$1" in
        --force)
            FORCE_FLAG="--force"
            shift
            ;;
        --parent-id=*)
            PARENT_ID="--parent-id=${1#*=}"
            shift
            ;;
        --timeout=*)
            TIMEOUT="--timeout=${1#*=}"
            shift
            ;;
        --workers=*)
            WORKERS="--workers=${1#*=}"
            shift
            ;;
        --batch-size=*)
            BATCH_SIZE="--batch-size=${1#*=}"
            shift
            ;;
        *)
            echo "Unknown option: $1"
            echo "Usage: $0 [--force] [--parent-id=ID] [--timeout=MINUTES] [--workers=NUM] [--batch-size=NUM]"
            exit 1
            ;;
    esac
done

# Run the upload script
echo "Starting upload process..."
echo "Folders in data/to_upload will be uploaded to Google Drive"
echo "Successfully uploaded folders will be moved to data/uploaded"
python gdrive_uploader_cli.py upload-all $FORCE_FLAG $PARENT_ID $TIMEOUT $WORKERS $BATCH_SIZE

# Deactivate virtual environment
deactivate
