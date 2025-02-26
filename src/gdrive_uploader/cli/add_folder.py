#!/usr/bin/env python3
"""
Command-line interface for adding a folder to the to_upload directory.
"""

import os
import sys
import argparse
from pathlib import Path

from gdrive_uploader.utils.file_utils import add_folder_to_upload

def main():
    """Main function to parse arguments and add the folder."""
    # Get the base directory of the package
    base_dir = Path(__file__).parent.parent.parent.parent.resolve()
    to_upload_dir = os.path.join(base_dir, 'data', 'to_upload')
    
    parser = argparse.ArgumentParser(
        description='Add a folder to the to_upload directory for later uploading to Google Drive'
    )
    parser.add_argument(
        'folder_path',
        help='Path to the folder to add'
    )
    parser.add_argument(
        '--move',
        action='store_true',
        help='Move the folder instead of copying it'
    )
    args = parser.parse_args()
    
    success = add_folder_to_upload(args.folder_path, to_upload_dir, args.move)
    if success:
        print(f"Folder is now ready to be uploaded using the upload-all command")
    
if __name__ == '__main__':
    main()
