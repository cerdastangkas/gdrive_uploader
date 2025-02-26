#!/usr/bin/env python3
"""
Script to automatically upload all folders inside the data/to_upload directory to Google Drive.
"""

import os
import sys
import argparse
import time
from tqdm import tqdm
from gdrive_uploader import (
    authenticate, 
    upload_folder, 
    is_folder_uploaded, 
    record_folder_upload,
    generate_folder_hash
)

# Path to the directory containing folders to upload
TO_UPLOAD_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', 'to_upload')

def get_folders_to_upload(force=False):
    """Get a list of folders to upload from the data/to_upload directory."""
    # Ensure the to_upload directory exists
    os.makedirs(TO_UPLOAD_DIR, exist_ok=True)
    
    # Get all items in the to_upload directory
    items = os.listdir(TO_UPLOAD_DIR)
    
    # Filter for directories only
    folders = []
    for item in items:
        item_path = os.path.join(TO_UPLOAD_DIR, item)
        if os.path.isdir(item_path):
            # If force is False, only include folders that haven't been uploaded yet
            if force or not is_folder_uploaded(item_path):
                folders.append(item_path)
    
    return folders

def upload_all_folders(parent_id=None, force=False):
    """Upload all folders in the data/to_upload directory to Google Drive."""
    # Get folders to upload
    folders = get_folders_to_upload(force)
    
    if not folders:
        print("No folders to upload found in data/to_upload directory.")
        if not force:
            print("Use --force to upload folders that have already been uploaded.")
        return
    
    print(f"Found {len(folders)} folder(s) to upload:")
    for i, folder in enumerate(folders):
        print(f"{i+1}. {os.path.basename(folder)}")
    
    try:
        # Authenticate with Google Drive
        service = authenticate()
        
        # Upload each folder
        for folder in folders:
            folder_name = os.path.basename(folder)
            print(f"\nUploading folder: {folder_name}")
            
            # Count total files and folders for progress tracking
            total_items = sum([len(files) + len(dirs) for _, dirs, files in os.walk(folder)])
            
            # Upload the folder with progress bar
            start_time = time.time()
            with tqdm(total=total_items, desc=f"Uploading {folder_name}", unit="item") as pbar:
                folder_id = upload_folder(service, folder, parent_id, pbar)
            
            # Record the upload in the CSV file
            record_folder_upload(folder, folder_id)
            
            elapsed_time = time.time() - start_time
            print(f"Upload complete for {folder_name}!")
            print(f"Folder ID in Google Drive: {folder_id}")
            print(f"Upload took {elapsed_time:.2f} seconds")
            print(f"You can access it at: https://drive.google.com/drive/folders/{folder_id}")
        
        print("\nAll folders have been uploaded successfully!")
        
    except Exception as e:
        print(f"An error occurred: {e}")
        sys.exit(1)

def main():
    """Main function to parse arguments and start the upload process."""
    parser = argparse.ArgumentParser(
        description='Upload all folders in the data/to_upload directory to Google Drive'
    )
    parser.add_argument(
        '--parent-id', 
        help='ID of the parent folder in Google Drive (optional)'
    )
    parser.add_argument(
        '--force', 
        action='store_true', 
        help='Force upload even if folders have been uploaded before'
    )
    args = parser.parse_args()
    
    upload_all_folders(args.parent_id, args.force)

if __name__ == '__main__':
    main()
