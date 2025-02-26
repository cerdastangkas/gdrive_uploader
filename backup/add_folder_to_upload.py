#!/usr/bin/env python3
"""
Script to add a folder to the data/to_upload directory for later uploading to Google Drive.
This script can copy or move a folder to the data/to_upload directory.
"""

import os
import sys
import argparse
import shutil
from pathlib import Path

# Path to the directory containing folders to upload
TO_UPLOAD_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', 'to_upload')

def add_folder(folder_path, move=False):
    """
    Add a folder to the data/to_upload directory.
    
    Args:
        folder_path: Path to the folder to add
        move: If True, move the folder instead of copying it
    """
    try:
        # Convert to Path object for better path handling
        folder_path = Path(folder_path).expanduser().resolve()
        
        # Check if the folder exists
        if not folder_path.exists():
            print(f"Error: Folder '{folder_path}' does not exist.")
            print("Please check the path and try again.")
            print(f"Current working directory: {os.getcwd()}")
            return False
        
        # Check if it's a directory
        if not folder_path.is_dir():
            print(f"Error: '{folder_path}' is not a directory.")
            return False
        
        # Ensure the to_upload directory exists
        os.makedirs(TO_UPLOAD_DIR, exist_ok=True)
        
        # Get the folder name
        folder_name = folder_path.name
        
        # Destination path
        dest_path = Path(TO_UPLOAD_DIR) / folder_name
        
        # Check if a folder with the same name already exists in the to_upload directory
        if dest_path.exists():
            print(f"Error: A folder named '{folder_name}' already exists in the data/to_upload directory.")
            return False
        
        # Copy or move the folder
        if move:
            print(f"Moving folder '{folder_name}' to data/to_upload...")
            shutil.move(str(folder_path), str(dest_path))
            print(f"Folder moved successfully.")
        else:
            print(f"Copying folder '{folder_name}' to data/to_upload...")
            shutil.copytree(str(folder_path), str(dest_path))
            print(f"Folder copied successfully.")
        
        return True
    except Exception as e:
        print(f"Error: {e}")
        return False

def main():
    """Main function to parse arguments and add the folder."""
    parser = argparse.ArgumentParser(
        description='Add a folder to the data/to_upload directory for later uploading to Google Drive'
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
    
    success = add_folder(args.folder_path, args.move)
    if success:
        print(f"Folder is now ready to be uploaded using upload_all_to_gdrive.sh")
    
if __name__ == '__main__':
    main()
