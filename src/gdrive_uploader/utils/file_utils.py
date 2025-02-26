#!/usr/bin/env python3
"""
Utility functions for file operations.
"""

import os
import shutil
from pathlib import Path

def get_folder_size(folder_path):
    """Calculate the total size of a folder in bytes."""
    total_size = 0
    for dirpath, dirnames, filenames in os.walk(folder_path):
        for filename in filenames:
            file_path = os.path.join(dirpath, filename)
            if os.path.exists(file_path):  # Check if file exists (in case of symlinks)
                total_size += os.path.getsize(file_path)
    return total_size


def add_folder_to_upload(folder_path, to_upload_dir, move=False):
    """
    Add a folder to the to_upload directory.
    
    Args:
        folder_path: Path to the folder to add
        to_upload_dir: Path to the directory where folders to upload are stored
        move: If True, move the folder instead of copying it
    
    Returns:
        bool: True if successful, False otherwise
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
        os.makedirs(to_upload_dir, exist_ok=True)
        
        # Get the folder name
        folder_name = folder_path.name
        
        # Destination path
        dest_path = Path(to_upload_dir) / folder_name
        
        # Check if a folder with the same name already exists in the to_upload directory
        if dest_path.exists():
            print(f"Error: A folder named '{folder_name}' already exists in the upload directory.")
            return False
        
        # Copy or move the folder
        if move:
            print(f"Moving folder '{folder_name}' to upload directory...")
            shutil.move(str(folder_path), str(dest_path))
            print(f"Folder moved successfully.")
        else:
            print(f"Copying folder '{folder_name}' to upload directory...")
            shutil.copytree(str(folder_path), str(dest_path))
            print(f"Folder copied successfully.")
        
        return True
    except Exception as e:
        print(f"Error: {e}")
        return False
