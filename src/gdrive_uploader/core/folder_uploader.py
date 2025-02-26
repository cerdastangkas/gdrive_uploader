#!/usr/bin/env python3
"""
Core functionality for uploading folders to Google Drive.
This module handles the folder upload process and tracking.
"""

import os
import sys
import time
import hashlib
import datetime
import pandas as pd
from pathlib import Path
from tqdm import tqdm
import concurrent.futures
import threading

from gdrive_uploader.core.drive_api import (
    find_or_create_folder, 
    upload_file, 
    batch_create_folders, 
    parallel_upload_files,
    get_service
)
from gdrive_uploader.utils.formatting import format_size

# Path to the CSV file that tracks uploaded folders
UPLOADS_CSV = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))), 'data', 'uploaded_folders.csv')

# Ensure the data directory exists
os.makedirs(os.path.dirname(UPLOADS_CSV), exist_ok=True)


def generate_folder_hash(folder_path):
    """Generate a unique hash for a folder based on its path and modification time."""
    folder_path = os.path.abspath(folder_path)
    
    if not os.path.exists(folder_path):
        raise ValueError(f"Folder does not exist: {folder_path}")
    
    # Get the folder name and modification time
    folder_name = os.path.basename(folder_path)
    folder_mtime = os.path.getmtime(folder_path)
    
    # Create a hash based on the folder path and modification time
    hash_input = f"{folder_path}_{folder_mtime}"
    folder_hash = hashlib.md5(hash_input.encode()).hexdigest()
    
    return folder_hash


def is_folder_uploaded(folder_path):
    """Check if a folder has already been uploaded by looking at the CSV file."""
    if not os.path.exists(UPLOADS_CSV):
        return False
    
    try:
        # Generate a hash for the folder
        folder_hash = generate_folder_hash(folder_path)
        
        # Read the CSV file
        df = pd.read_csv(UPLOADS_CSV)
        
        # Check if the folder hash exists in the CSV
        return folder_hash in df['folder_hash'].values
    except Exception as e:
        print(f"Error checking if folder is uploaded: {e}")
        return False


def record_folder_upload(folder_path, drive_folder_id):
    """Record the folder upload in the CSV file."""
    try:
        folder_path = os.path.abspath(folder_path)
        folder_name = os.path.basename(folder_path)
        folder_hash = generate_folder_hash(folder_path)
        upload_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Create a new row for the CSV
        new_row = {
            'folder_path': folder_path,
            'folder_name': folder_name,
            'folder_hash': folder_hash,
            'drive_folder_id': drive_folder_id,
            'upload_time': upload_time
        }
        
        # If the CSV doesn't exist, create it with the new row
        if not os.path.exists(UPLOADS_CSV):
            df = pd.DataFrame([new_row])
            df.to_csv(UPLOADS_CSV, index=False)
            return True
        
        # Otherwise, append the new row to the existing CSV
        df = pd.read_csv(UPLOADS_CSV)
        
        # Check if the folder hash already exists
        if folder_hash in df['folder_hash'].values:
            # Update the existing row
            df.loc[df['folder_hash'] == folder_hash, 'drive_folder_id'] = drive_folder_id
            df.loc[df['folder_hash'] == folder_hash, 'upload_time'] = upload_time
        else:
            # Append the new row
            df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
        
        # Save the updated CSV
        df.to_csv(UPLOADS_CSV, index=False)
        return True
    except Exception as e:
        print(f"Error recording folder upload: {e}")
        return False


def upload_folder(service, folder_path, parent_id=None, progress_bar=None, max_workers=5):
    """Upload a folder and its contents to Google Drive with parallel processing."""
    folder_name = os.path.basename(folder_path)
    
    # Create the folder in Google Drive
    folder_id = find_or_create_folder(service, folder_name, parent_id)
    
    # Get all items in the folder
    file_items = []
    folder_items = []
    total_size = 0
    
    # First, collect all items and calculate total size
    for root, dirs, files in os.walk(folder_path):
        for file in files:
            file_path = os.path.join(root, file)
            rel_path = os.path.relpath(file_path, folder_path)
            size = os.path.getsize(file_path)
            total_size += size
            file_items.append({
                'path': file_path,
                'rel_path': rel_path,
                'size': size,
                'is_file': True
            })
        
        for dir in dirs:
            dir_path = os.path.join(root, dir)
            rel_path = os.path.relpath(dir_path, folder_path)
            folder_items.append({
                'path': dir_path,
                'rel_path': rel_path,
                'name': dir,
                'parent_path': os.path.dirname(rel_path) or '.',
                'is_file': False
            })
    
    # Sort folders by depth to ensure parent folders are created first
    folder_items.sort(key=lambda x: x['rel_path'].count(os.sep))
    
    # Group folders by parent path for batch creation
    folder_groups = {}
    for item in folder_items:
        parent_path = item['parent_path']
        if parent_path not in folder_groups:
            folder_groups[parent_path] = []
        folder_groups[parent_path].append(item)
    
    # Update progress bar if provided
    if progress_bar:
        progress_bar.total = len(file_items) + len(folder_items)
        progress_bar.refresh()
    
    # Create a dictionary to store folder IDs for quick lookup
    folder_ids = {'.': folder_id}
    
    # Create folders in batches, grouped by parent
    print(f"Creating {len(folder_items)} folders...")
    
    for parent_path, items in folder_groups.items():
        try:
            parent_id = folder_ids.get(parent_path)
            if not parent_id:
                # This shouldn't happen if folders are sorted correctly
                print(f"  Warning: Parent folder for {parent_path} not found. Using root folder.")
                parent_id = folder_id
            
            # Extract folder names for batch creation
            folder_names = [os.path.basename(item['path']) for item in items]
            
            # Create folders in batch
            created_folders = batch_create_folders(service, folder_names, parent_id)
            
            # Store folder IDs
            for item in items:
                folder_name = os.path.basename(item['path'])
                if folder_name in created_folders:
                    folder_ids[item['rel_path']] = created_folders[folder_name]
                    if progress_bar:
                        progress_bar.update(1)
                else:
                    print(f"  Warning: Failed to create folder {folder_name}")
                
        except Exception as e:
            print(f"  Error creating folders in {parent_path}: {str(e)}")
            # Try to create folders one by one as fallback
            for item in items:
                try:
                    folder_name = os.path.basename(item['path'])
                    new_id = find_or_create_folder(service, folder_name, parent_id)
                    folder_ids[item['rel_path']] = new_id
                    if progress_bar:
                        progress_bar.update(1)
                except Exception as e2:
                    print(f"  Error creating folder {folder_name}: {str(e2)}")
    
    # Upload files in parallel
    print(f"Uploading {len(file_items)} files ({format_size(total_size)})...")
    
    # Split files into batches for parallel processing
    batch_size = 100  # Process files in batches to avoid memory issues
    for i in range(0, len(file_items), batch_size):
        batch_files = file_items[i:i+batch_size]
        
        # Upload files in parallel
        try:
            results = parallel_upload_files(batch_files, folder_ids, max_workers=max_workers)
            
            # Process results
            for rel_path, result in results.items():
                if result['success']:
                    print(f"  Uploaded: {rel_path} ({format_size(result['item']['size'])})")
                else:
                    print(f"  Error uploading {rel_path}: {result['error']}")
                    # Try to upload the file again directly if parallel upload failed
                    try:
                        item = result['item']
                        parent_path = os.path.dirname(item['rel_path'])
                        if not parent_path:
                            parent_path = '.'
                        
                        parent_folder_id = folder_ids.get(parent_path)
                        if parent_folder_id:
                            print(f"  Retrying upload of {rel_path}...")
                            file_id = upload_file(service, item['path'], parent_folder_id)
                            print(f"  Successfully uploaded on retry: {rel_path}")
                    except Exception as e:
                        print(f"  Failed to upload {rel_path} on retry: {str(e)}")
                
                if progress_bar:
                    progress_bar.update(1)
        except Exception as e:
            print(f"  Error in parallel upload batch: {str(e)}")
            # Fall back to sequential upload for this batch
            print(f"  Falling back to sequential upload for batch...")
            for item in batch_files:
                try:
                    parent_path = os.path.dirname(item['rel_path'])
                    if not parent_path:
                        parent_path = '.'
                    
                    parent_folder_id = folder_ids.get(parent_path)
                    if parent_folder_id:
                        file_id = upload_file(service, item['path'], parent_folder_id)
                        print(f"  Uploaded: {item['rel_path']} ({format_size(item['size'])})")
                    else:
                        print(f"  Error: Parent folder not found for {item['rel_path']}")
                except Exception as e:
                    print(f"  Error uploading {item['rel_path']}: {str(e)}")
                
                if progress_bar:
                    progress_bar.update(1)
    
    return folder_id
