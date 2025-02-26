#!/usr/bin/env python3
"""
Example script demonstrating how to use the Google Drive Folder Uploader programmatically.
"""

import os
import sys
from gdrive_uploader import authenticate, upload_folder, is_folder_uploaded, record_folder_upload
from tqdm import tqdm

def main():
    # Path to the folder you want to upload
    folder_path = os.path.expanduser("~/Documents/FolderToUpload")
    
    # Optional: ID of a folder in Google Drive where you want to upload
    # Leave as None to upload to the root of your Google Drive
    parent_folder_id = None
    
    # Force upload even if the folder has been uploaded before
    force_upload = False
    
    # Check if the folder exists
    if not os.path.exists(folder_path):
        print(f"Error: Folder '{folder_path}' does not exist.")
        print("Please modify this script to point to a valid folder.")
        sys.exit(1)
    
    # Check if the folder has already been uploaded
    if not force_upload and is_folder_uploaded(folder_path):
        print(f"Folder '{folder_path}' has already been uploaded.")
        print("Set force_upload = True to upload it again.")
        sys.exit(0)
    
    try:
        # Authenticate with Google Drive
        service = authenticate()
        
        print(f"Uploading folder: {folder_path}")
        
        # Count total files and folders for progress tracking
        total_items = sum([len(files) + len(dirs) for _, dirs, files in os.walk(folder_path)])
        
        # Upload the folder with progress bar
        with tqdm(total=total_items, desc="Uploading", unit="item") as pbar:
            folder_id = upload_folder(service, folder_path, parent_folder_id, pbar)
        
        # Record the upload in the CSV file
        record_folder_upload(folder_path, folder_id)
        
        print(f"\nUpload complete!")
        print(f"Folder ID in Google Drive: {folder_id}")
        print(f"You can access it at: https://drive.google.com/drive/folders/{folder_id}")
        
    except Exception as e:
        print(f"An error occurred: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
