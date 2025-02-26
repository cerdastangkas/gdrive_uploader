# Google Drive Folder Uploader

A Python tool to upload folders from your local machine to Google Drive while preserving the folder structure.

## Features

- Upload entire folders to Google Drive
- Preserve folder structure
- Show progress during upload
- Support for authentication with Google Drive API
- Option to specify a parent folder in Google Drive
- **Prevents duplicate uploads by tracking uploaded folders in a CSV file**
- **Batch upload all folders from a designated directory**

## Prerequisites

- Python 3.6 or higher
- Google Cloud Platform account
- Google Drive API enabled
- OAuth 2.0 credentials

## Installation

1. Clone this repository or download the files
2. Install the required dependencies:

```bash
pip install -r requirements.txt
```

## Setup Google Drive API

1. Go to the [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Enable the Google Drive API
4. Create OAuth 2.0 credentials (Desktop application)
5. Download the credentials JSON file
6. Save the file as `credentials.json` in the same directory as the script

## Project Structure

The project is organized into the following modules:

```
gdrive_uploader/
├── data/                  # Directory for data files
│   ├── to_upload/         # Place folders to upload here
│   └── uploaded_folders.csv # Tracks uploaded folders
├── src/                   # Source code
│   └── gdrive_uploader/   # Main package
│       ├── core/          # Core functionality
│       │   ├── drive_api.py      # Google Drive API interactions
│       │   └── folder_uploader.py # Folder upload functionality
│       ├── utils/         # Utility functions
│       │   ├── file_utils.py     # File operations
│       │   └── formatting.py     # Output formatting
│       └── cli/           # Command-line interfaces
│           ├── add_folder.py     # Add folder CLI
│           ├── manage_uploads.py # Manage uploads CLI
│           └── upload_all.py     # Upload all folders CLI
├── backup/                # Backup of old files
├── venv/                  # Virtual environment (created automatically)
├── add_folder.sh          # Shell script to add folders
├── gdrive_uploader_cli.py # Main CLI entry point
├── setup.py               # Package setup file
├── requirements.txt       # Dependencies
└── upload_all_to_gdrive.sh # Shell script to upload all folders
```

## Usage

### Using the Command-Line Interface

The main CLI provides several commands for working with the Google Drive Uploader:

```bash
# Upload all folders in data/to_upload directory
python gdrive_uploader_cli.py upload-all [--parent-id=ID] [--force] [--timeout=MINUTES]

# Add a folder to the to_upload directory
python gdrive_uploader_cli.py add-folder [--move] FOLDER_PATH

# Manage uploaded folders
python gdrive_uploader_cli.py manage list
python gdrive_uploader_cli.py manage delete INDEX
python gdrive_uploader_cli.py manage clear
```

### Using Shell Scripts

For convenience, shell scripts are provided for common operations:

```bash
# Upload all folders in data/to_upload directory
./upload_all_to_gdrive.sh [--parent-id=ID] [--force] [--timeout=MINUTES]

# Add a folder to the to_upload directory
./add_folder.sh [--move] FOLDER_PATH
```

### Options

- `--parent-id=ID`: Upload to a specific folder in Google Drive (optional)
- `--force`: Force upload even if folders have been uploaded before (optional)
- `--timeout=MINUTES`: Maximum time in minutes to allow the upload process to run (optional)
- `--move`: Move the folder instead of copying it when adding to the upload queue (optional)

### Examples

```bash
# Upload all folders to the root of Google Drive
./upload_all_to_gdrive.sh

# Upload all folders to a specific folder in Google Drive
./upload_all_to_gdrive.sh --parent-id=1a2b3c4d5e6f7g8h9i0j

# Force upload all folders even if they have been uploaded before
./upload_all_to_gdrive.sh --force

# Upload all folders with a 60-minute timeout
./upload_all_to_gdrive.sh --timeout=60

# Add a folder to the upload queue (copy)
./add_folder.sh ~/Documents/MyFolder

# Add a folder to the upload queue (move)
./add_folder.sh --move ~/Documents/MyFolder
```

### How to Use the Batch Upload Feature

1. Place the folders you want to upload in the `data/to_upload` directory
   - You can do this manually or use the `add_folder.sh` script
2. Run the `upload_all_to_gdrive.sh` shell script
3. The script will automatically upload all folders in the directory that haven't been uploaded before
4. Use the `--force` option to upload folders that have already been uploaded

## Duplicate Upload Prevention

The tool keeps track of uploaded folders in a CSV file located at `data/uploaded_folders.csv`. Before uploading a folder, it checks if the folder has already been uploaded by comparing a unique hash generated from the folder path and its last modification time.

If a folder has already been uploaded, the tool will inform you and exit. You can use the `--force` option to upload the folder again if needed.

### Managing Uploaded Folders

You can view and manage the uploaded folders using the manage command:

```bash
# List all uploaded folders
python gdrive_uploader_cli.py manage list

# Delete an upload entry by index
python gdrive_uploader_cli.py manage delete INDEX

# Clear all upload entries
python gdrive_uploader_cli.py manage clear
```

## Workflow Management

The tool provides a streamlined workflow for managing your uploads:

### Automatic Folder Organization

After successful upload, folders are automatically moved from `data/to_upload` to `data/uploaded` to keep your workspace organized:

1. Place folders to be uploaded in the `data/to_upload` directory
2. Run the upload command: `python gdrive_uploader_cli.py upload-all`
3. Successfully uploaded folders are automatically moved to `data/uploaded`
4. Failed or interrupted uploads remain in `data/to_upload` for retry

This prevents accidental re-uploading of the same folders and provides a clear record of what has been uploaded.

### Upload History

## Workflow Scripts

The tool includes several scripts to streamline your workflow:

- **upload_all_to_gdrive.sh**: Uploads all folders in `data/to_upload` to Google Drive
  ```bash
  ./upload_all_to_gdrive.sh [--workers=5] [--batch-size=100] [--force]
  ```

- **check_upload_status.sh**: Shows the status of pending and completed uploads
  ```bash
  ./check_upload_status.sh
  ```

- **add_folder.sh**: Adds a folder to the upload queue
  ```bash
  ./add_folder.sh [--move] /path/to/folder
  ```

## Performance Optimization

The uploader now includes several performance optimizations to speed up the upload process:

### Parallel Uploads

By default, the tool uses 5 parallel workers to upload files simultaneously. You can adjust this with the `--workers` parameter:

```bash
# Use 10 parallel workers for faster uploads
python gdrive_uploader_cli.py upload-all --workers 10

# Use fewer workers on systems with limited resources
python gdrive_uploader_cli.py upload-all --workers 3
```

This multi-threaded approach can significantly improve upload speeds, especially for folders with many small files. Each worker operates independently, allowing multiple files to be uploaded simultaneously.

### Batch Processing

Files are processed in batches (default 100) to optimize memory usage. You can adjust the batch size:

```bash
# Use larger batches for faster processing
python gdrive_uploader_cli.py upload-all --batch-size 200

# Use smaller batches for systems with limited memory
python gdrive_uploader_cli.py upload-all --batch-size 50
```

Batch processing helps manage memory usage while still maintaining good performance. The tool processes files in chunks, which prevents memory exhaustion when uploading very large folders.

### Optimized Chunk Sizes

The tool automatically optimizes chunk sizes based on file size:
- Large files (>100MB): 10MB chunks
- Medium files (10-100MB): 5MB chunks
- Small files (<1MB): 256KB chunks
- Other files: 1MB chunks

This dynamic chunk sizing ensures optimal upload speeds for different file types. Larger chunks reduce overhead for big files, while smaller chunks improve reliability for small files.

### Folder Caching

The tool caches folder IDs to reduce redundant API calls, significantly speeding up uploads with many nested folders. This optimization particularly helps with:

- Deeply nested folder structures
- Folders with many subfolders
- Repeated uploads to the same destination

By avoiding repeated API calls to check if folders exist, the upload process becomes much faster.

## Robust Error Handling

The tool now includes improved error handling to ensure uploads complete successfully:

### Automatic Retries

Failed uploads are automatically retried with exponential backoff:

- First retry: 2 seconds delay
- Second retry: 4 seconds delay
- Third retry: 8 seconds delay
- And so on, up to a maximum of 60 seconds

This helps overcome temporary network issues and API rate limits without manual intervention.

#### Duplicate Prevention

The retry mechanism includes intelligent duplicate detection:

- Before each upload, the tool checks if the file already exists in the destination
- If a file with the same name exists, it reuses the existing file ID instead of creating a duplicate
- After a failed upload attempt, it checks if the file was actually created despite the error
- This ensures no duplicate files are created even if network errors occur during upload

### Fallback Mechanisms

The tool implements several fallback strategies:

- If parallel uploads fail, it falls back to sequential uploads
- If batch folder creation fails, it falls back to individual folder creation
- If a folder already exists, it reuses the existing folder instead of creating a new one

### API Error Handling

Special handling for Google Drive API errors:

- Rate limit errors (429): Automatic retry with backoff
- Server errors (500, 502, 503, 504): Automatic retry with backoff
- Authentication errors: Clear instructions for resolving token issues

### Detailed Logging

Comprehensive error reporting helps troubleshoot issues:

- Specific error messages for each failure type
- Progress tracking for large uploads
- Upload speed and time statistics

## First-time Authentication

When you run the script for the first time, it will open a browser window asking you to log in to your Google account and grant permission to access your Google Drive. After successful authentication, a token file will be saved locally for future use.

## Notes

- Large folders may take some time to upload depending on your internet connection
- The script will not upload files that are already in Google Drive with the same name in the same location
- If you change the API scopes, delete the `token.pickle` file to force re-authentication
