#!/usr/bin/env python3
"""
Google Drive Folder Uploader

This script allows you to upload a local folder and its contents to Google Drive.
It maintains the folder structure and shows progress during upload.
It also tracks uploaded folders in a CSV file to prevent duplicate uploads.
"""

import os
import sys
import argparse
import hashlib
import datetime
import pandas as pd
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload
from tqdm import tqdm
import pickle
import time

# If modifying these scopes, delete the file token.pickle.
SCOPES = ['https://www.googleapis.com/auth/drive']

# Path to the CSV file that tracks uploaded folders
UPLOADS_CSV = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', 'uploaded_folders.csv')

# Ensure the data directory exists
os.makedirs(os.path.dirname(UPLOADS_CSV), exist_ok=True)


def authenticate():
    """Authenticate with Google Drive API and return the service."""
    creds = None
    # The file token.pickle stores the user's access and refresh tokens
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not os.path.exists('credentials.json'):
                print("Error: credentials.json file not found.")
                print("Please download your OAuth 2.0 credentials from the Google Cloud Console")
                print("and save them as 'credentials.json' in the same directory as this script.")
                sys.exit(1)
                
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        
        # Save the credentials for the next run
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)

    return build('drive', 'v3', credentials=creds)


def find_or_create_folder(service, folder_name, parent_id=None):
    """Find a folder in Google Drive, or create it if it doesn't exist."""
    query = f"name='{folder_name}' and mimeType='application/vnd.google-apps.folder'"
    if parent_id:
        query += f" and '{parent_id}' in parents"
    query += " and trashed=false"
    
    results = service.files().list(q=query, spaces='drive', fields='files(id, name)').execute()
    items = results.get('files', [])
    
    if items:
        return items[0]['id']
    else:
        # Folder doesn't exist, create it
        file_metadata = {
            'name': folder_name,
            'mimeType': 'application/vnd.google-apps.folder'
        }
        if parent_id:
            file_metadata['parents'] = [parent_id]
        
        folder = service.files().create(body=file_metadata, fields='id').execute()
        return folder.get('id')


def upload_file(service, file_path, parent_id=None):
    """Upload a file to Google Drive."""
    file_name = os.path.basename(file_path)
    file_size = os.path.getsize(file_path)
    file_metadata = {'name': file_name}
    if parent_id:
        file_metadata['parents'] = [parent_id]
    
    # Use different chunk sizes based on file size for better performance
    chunk_size = 1024 * 1024  # Default: 1MB
    if file_size > 100 * 1024 * 1024:  # If file > 100MB
        chunk_size = 5 * 1024 * 1024  # Use 5MB chunks
    
    media = MediaFileUpload(file_path, resumable=True, chunksize=chunk_size)
    
    # Create the request
    request = service.files().create(body=file_metadata, media_body=media, fields='id')
    
    # Execute the request and handle errors with retry
    response = None
    retries = 0
    max_retries = 3
    
    while response is None and retries < max_retries:
        try:
            response = request.execute()
        except HttpError as e:
            if e.resp.status in [429, 500, 502, 503, 504]:  # Retry on rate limit or server errors
                retries += 1
                wait_time = 2 ** retries  # Exponential backoff
                print(f"  Error uploading {file_name}. Retrying in {wait_time} seconds...")
                time.sleep(wait_time)
            else:
                raise
    
    if response is None:
        raise Exception(f"Failed to upload {file_name} after {max_retries} retries")
        
    return response.get('id')


def upload_folder(service, folder_path, parent_id=None, progress_bar=None):
    """Upload a folder and its contents to Google Drive."""
    folder_name = os.path.basename(folder_path)
    
    # Create the folder in Google Drive
    folder_id = find_or_create_folder(service, folder_name, parent_id)
    
    # Get all items in the folder
    items = []
    total_size = 0
    
    # First, collect all items and calculate total size
    for root, dirs, files in os.walk(folder_path):
        for file in files:
            file_path = os.path.join(root, file)
            rel_path = os.path.relpath(file_path, folder_path)
            size = os.path.getsize(file_path)
            total_size += size
            items.append({
                'path': file_path,
                'rel_path': rel_path,
                'size': size,
                'is_file': True
            })
        
        for dir in dirs:
            dir_path = os.path.join(root, dir)
            rel_path = os.path.relpath(dir_path, folder_path)
            items.append({
                'path': dir_path,
                'rel_path': rel_path,
                'size': 0,
                'is_file': False
            })
    
    # Sort items so that directories come before files in the same directory
    # This ensures parent directories are created before trying to upload files to them
    items.sort(key=lambda x: (x['rel_path'].count(os.sep), x['is_file']))
    
    # Update progress bar if provided
    if progress_bar:
        progress_bar.total = len(items)
        progress_bar.refresh()
    
    # Create a dictionary to store folder IDs for quick lookup
    folder_ids = {'.': folder_id}
    
    # Upload each item
    for item in items:
        try:
            if item['is_file']:
                # Get the parent folder ID
                parent_path = os.path.dirname(item['rel_path'])
                if not parent_path:
                    parent_path = '.'
                
                parent_folder_id = folder_ids.get(parent_path)
                if not parent_folder_id:
                    # This shouldn't happen if items are sorted correctly
                    print(f"  Warning: Parent folder for {item['rel_path']} not found. Using root folder.")
                    parent_folder_id = folder_id
                
                # Upload file
                file_id = upload_file(service, item['path'], parent_folder_id)
                print(f"  Uploaded: {item['rel_path']} ({format_size(item['size'])})")
            else:
                # Create folder
                parent_path = os.path.dirname(item['rel_path'])
                if not parent_path:
                    parent_path = '.'
                
                parent_folder_id = folder_ids.get(parent_path)
                if not parent_folder_id:
                    # This shouldn't happen if items are sorted correctly
                    print(f"  Warning: Parent folder for {item['rel_path']} not found. Using root folder.")
                    parent_folder_id = folder_id
                
                # Create the folder in Google Drive
                new_folder_id = find_or_create_folder(service, os.path.basename(item['path']), parent_folder_id)
                folder_ids[item['rel_path']] = new_folder_id
                print(f"  Created folder: {item['rel_path']}")
        except Exception as e:
            print(f"  Error processing {item['rel_path']}: {str(e)}")
        
        if progress_bar:
            progress_bar.update(1)
    
    return folder_id


def format_size(size_bytes):
    """Format file size in a human-readable format."""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    elif size_bytes < 1024 * 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.1f} MB"
    else:
        return f"{size_bytes / (1024 * 1024 * 1024):.1f} GB"


def generate_folder_hash(folder_path):
    """Generate a unique hash for a folder based on its path and modification time."""
    folder_path = os.path.abspath(folder_path)
    
    # Get the folder's last modification time
    mod_time = os.path.getmtime(folder_path)
    
    # Create a hash from the folder path and modification time
    hash_input = f"{folder_path}_{mod_time}"
    return hashlib.md5(hash_input.encode()).hexdigest()


def is_folder_uploaded(folder_path):
    """Check if a folder has already been uploaded by looking at the CSV file."""
    folder_path = os.path.abspath(folder_path)
    folder_hash = generate_folder_hash(folder_path)
    
    # If the CSV file doesn't exist yet, the folder hasn't been uploaded
    if not os.path.exists(UPLOADS_CSV):
        return False
    
    try:
        # Read the CSV file
        df = pd.read_csv(UPLOADS_CSV)
        
        # Check if the folder hash exists in the CSV
        return folder_hash in df['folder_hash'].values
    except Exception as e:
        print(f"Warning: Error checking upload status: {e}")
        return False


def record_folder_upload(folder_path, drive_folder_id):
    """Record the folder upload in the CSV file."""
    folder_path = os.path.abspath(folder_path)
    folder_hash = generate_folder_hash(folder_path)
    folder_name = os.path.basename(folder_path)
    upload_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    # Prepare the new row data
    new_data = {
        'folder_path': folder_path,
        'folder_name': folder_name,
        'folder_hash': folder_hash,
        'drive_folder_id': drive_folder_id,
        'upload_time': upload_time,
        'uploaded': True
    }
    
    # If the CSV file exists, append to it
    if os.path.exists(UPLOADS_CSV):
        try:
            df = pd.read_csv(UPLOADS_CSV)
            
            # Check if this folder hash already exists
            if folder_hash in df['folder_hash'].values:
                # Update the existing entry
                df.loc[df['folder_hash'] == folder_hash, 'drive_folder_id'] = drive_folder_id
                df.loc[df['folder_hash'] == folder_hash, 'upload_time'] = upload_time
                df.loc[df['folder_hash'] == folder_hash, 'uploaded'] = True
            else:
                # Append the new entry
                df = pd.concat([df, pd.DataFrame([new_data])], ignore_index=True)
        except Exception as e:
            print(f"Warning: Error updating CSV: {e}")
            # If there's an error, create a new DataFrame
            df = pd.DataFrame([new_data])
    else:
        # Create a new DataFrame
        df = pd.DataFrame([new_data])
    
    # Save the DataFrame to CSV
    try:
        df.to_csv(UPLOADS_CSV, index=False)
    except Exception as e:
        print(f"Warning: Error saving CSV: {e}")


def main():
    """Main function to parse arguments and start the upload process."""
    parser = argparse.ArgumentParser(description='Upload a folder to Google Drive')
    parser.add_argument('folder_path', help='Path to the folder to upload')
    parser.add_argument('--parent-id', help='ID of the parent folder in Google Drive (optional)')
    parser.add_argument('--force', action='store_true', help='Force upload even if the folder has been uploaded before')
    args = parser.parse_args()
    
    folder_path = os.path.abspath(args.folder_path)
    
    if not os.path.exists(folder_path):
        print(f"Error: Folder '{folder_path}' does not exist.")
        sys.exit(1)
    
    if not os.path.isdir(folder_path):
        print(f"Error: '{folder_path}' is not a directory.")
        sys.exit(1)
    
    # Check if the folder has already been uploaded
    if not args.force and is_folder_uploaded(folder_path):
        print(f"Folder '{folder_path}' has already been uploaded.")
        print("Use --force to upload it again.")
        sys.exit(0)
    
    try:
        service = authenticate()
        
        print(f"Uploading folder: {folder_path}")
        print("This may take some time depending on the folder size and your internet connection.")
        
        # Count total files and folders for progress tracking
        total_items = sum([len(files) + len(dirs) for _, dirs, files in os.walk(folder_path)])
        
        with tqdm(total=total_items, desc="Uploading", unit="item") as pbar:
            folder_id = upload_folder(service, folder_path, args.parent_id, pbar)
        
        # Record the upload in the CSV file
        record_folder_upload(folder_path, folder_id)
        
        print(f"\nUpload complete!")
        print(f"Folder ID in Google Drive: {folder_id}")
        print(f"You can access it at: https://drive.google.com/drive/folders/{folder_id}")
        
    except HttpError as error:
        print(f"An error occurred: {error}")
        sys.exit(1)


if __name__ == '__main__':
    main()
