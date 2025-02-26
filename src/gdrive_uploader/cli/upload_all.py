#!/usr/bin/env python3
"""
Command-line interface for uploading all folders in the to_upload directory.
"""

import os
import sys
import time
import signal
import argparse
import shutil
from tqdm import tqdm
from pathlib import Path

from gdrive_uploader.core.drive_api import authenticate
from gdrive_uploader.core.folder_uploader import upload_folder, is_folder_uploaded, record_folder_upload
from gdrive_uploader.utils.formatting import format_size
from gdrive_uploader.utils.file_utils import get_folder_size

# Global variable to track if timeout occurred
timeout_occurred = False

def timeout_handler(signum, frame):
    """Handle timeout signal."""
    global timeout_occurred
    timeout_occurred = True
    print("\n\nTimeout reached! The upload is taking too long.")
    print("The script will finish the current file and then exit.")
    print("You can run the script again later to continue uploading.")


def get_folders_to_upload(to_upload_dir, force=False):
    """Get a list of folders to upload from the to_upload directory."""
    # Ensure the to_upload directory exists
    os.makedirs(to_upload_dir, exist_ok=True)
    
    # Get all items in the to_upload directory
    items = os.listdir(to_upload_dir)
    
    # Filter for directories only
    folders = []
    for item in items:
        item_path = os.path.join(to_upload_dir, item)
        if os.path.isdir(item_path):
            # If force is False, only include folders that haven't been uploaded yet
            if force or not is_folder_uploaded(item_path):
                # Calculate folder size
                size = get_folder_size(item_path)
                folders.append({
                    'path': item_path,
                    'name': item,
                    'size': size
                })
    
    return folders


def upload_all_folders(to_upload_dir, parent_id=None, force=False, timeout=None, workers=5, batch_size=100):
    """Upload all folders in the to_upload directory to Google Drive."""
    global timeout_occurred
    
    # Set timeout handler if timeout is specified
    if timeout:
        signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(timeout * 60)  # Convert minutes to seconds
    
    # Create uploaded directory if it doesn't exist
    base_dir = Path(to_upload_dir).parent.resolve()
    uploaded_dir = os.path.join(base_dir, 'uploaded')
    os.makedirs(uploaded_dir, exist_ok=True)
    
    # Get folders to upload
    folders = get_folders_to_upload(to_upload_dir, force)
    
    if not folders:
        print("No folders to upload found in the upload directory.")
        if not force:
            print("Use --force to upload folders that have already been uploaded.")
        return
    
    # Sort folders by size (smallest first)
    folders.sort(key=lambda x: x['size'])
    
    print(f"Found {len(folders)} folder(s) to upload:")
    for i, folder in enumerate(folders):
        print(f"{i+1}. {folder['name']} ({format_size(folder['size'])})")
    
    try:
        # Authenticate with Google Drive
        print("\nAuthenticating with Google Drive...")
        service = authenticate()
        print("Authentication successful!")
        
        # Upload each folder
        for i, folder in enumerate(folders):
            if timeout_occurred:
                print("\nStopping upload process due to timeout.")
                break
                
            folder_name = folder['name']
            folder_path = folder['path']
            folder_size = folder['size']
            
            print(f"\n[{i+1}/{len(folders)}] Uploading folder: {folder_name} ({format_size(folder_size)})")
            
            # Count total items for progress tracking
            total_items = sum([len(files) + len(dirs) for _, dirs, files in os.walk(folder_path)])
            
            print(f"Total items to upload: {total_items}")
            print(f"Starting upload at: {time.strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"Using {workers} parallel workers and batch size of {batch_size}")
            
            # Upload the folder with progress bar
            start_time = time.time()
            with tqdm(total=total_items, desc=f"Uploading {folder_name}", unit="item") as pbar:
                folder_id = upload_folder(service, folder_path, parent_id, pbar, max_workers=workers)
            
            # Record the upload in the CSV file
            if not timeout_occurred:
                record_folder_upload(folder_path, folder_id)
                
                elapsed_time = time.time() - start_time
                print(f"Upload complete for {folder_name}!")
                print(f"Folder ID in Google Drive: {folder_id}")
                print(f"Upload took {elapsed_time:.2f} seconds ({elapsed_time/60:.2f} minutes)")
                print(f"Upload speed: {folder_size/elapsed_time/1024:.2f} KB/s")
                print(f"You can access it at: https://drive.google.com/drive/folders/{folder_id}")
                
                # Move the folder to the uploaded directory
                target_path = os.path.join(uploaded_dir, folder_name)
                if os.path.exists(target_path):
                    # If the folder already exists in the uploaded directory, append a timestamp
                    timestamp = time.strftime("%Y%m%d%H%M%S")
                    target_path = os.path.join(uploaded_dir, f"{folder_name}_{timestamp}")
                
                print(f"Moving folder to {target_path}...")
                try:
                    shutil.move(folder_path, target_path)
                    print(f"Folder moved successfully to {target_path}")
                except Exception as e:
                    print(f"Error moving folder: {str(e)}")
                    print(f"The folder remains in the to_upload directory.")
            else:
                print(f"Upload of {folder_name} was interrupted due to timeout.")
                print(f"Partial content may have been uploaded. Run the script again to continue.")
        
        if not timeout_occurred:
            print("\nAll folders have been uploaded successfully!")
        
    except KeyboardInterrupt:
        print("\n\nUpload process interrupted by user.")
        print("Partial content may have been uploaded. Run the script again to continue.")
        sys.exit(1)
    except Exception as e:
        print(f"\nAn error occurred: {e}")
        sys.exit(1)
    finally:
        # Reset the alarm
        if timeout:
            signal.alarm(0)


def main():
    """Main function to parse arguments and start the upload process."""
    # Get the base directory of the package
    base_dir = Path(__file__).parent.parent.parent.parent.resolve()
    to_upload_dir = os.path.join(base_dir, 'data', 'to_upload')
    
    parser = argparse.ArgumentParser(
        description='Upload all folders in the to_upload directory to Google Drive'
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
    parser.add_argument(
        '--timeout',
        type=int,
        help='Maximum time in minutes to allow the upload process to run'
    )
    parser.add_argument(
        '--workers',
        type=int,
        default=5,
        help='Number of parallel upload workers (default: 5)'
    )
    parser.add_argument(
        '--batch-size',
        type=int,
        default=100,
        help='Batch size for file uploads (default: 100)'
    )
    args = parser.parse_args()
    
    upload_all_folders(
        to_upload_dir, 
        args.parent_id, 
        args.force, 
        args.timeout,
        args.workers,
        args.batch_size
    )


if __name__ == '__main__':
    main()
