#!/usr/bin/env python3
"""
Core functionality for Google Drive API interactions.
This module handles authentication and basic Drive operations.
"""

import os
import sys
import time
import pickle
import hashlib
import mimetypes
from pathlib import Path
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload
import concurrent.futures
import threading

# If modifying these scopes, delete the file token.pickle.
SCOPES = ['https://www.googleapis.com/auth/drive']

# Thread-local storage for service objects
thread_local = threading.local()

def get_service():
    """Get a thread-local service object."""
    if not hasattr(thread_local, "service"):
        thread_local.service = authenticate()
    return thread_local.service

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

    # Build with higher cache size and increased timeout
    return build('drive', 'v3', credentials=creds, cache_discovery=True)


# Cache for folder IDs to avoid redundant API calls
folder_cache = {}

def find_or_create_folder(service, folder_name, parent_id=None):
    """Find a folder in Google Drive, or create it if it doesn't exist."""
    # Create a cache key
    cache_key = f"{folder_name}_{parent_id}"
    
    # Check if the folder ID is in the cache
    if cache_key in folder_cache:
        return folder_cache[cache_key]
    
    query = f"name='{folder_name}' and mimeType='application/vnd.google-apps.folder'"
    if parent_id:
        query += f" and '{parent_id}' in parents"
    query += " and trashed=false"
    
    results = service.files().list(q=query, spaces='drive', fields='files(id, name)').execute()
    items = results.get('files', [])
    
    if items:
        folder_id = items[0]['id']
        # Cache the folder ID
        folder_cache[cache_key] = folder_id
        return folder_id
    else:
        # Folder doesn't exist, create it
        file_metadata = {
            'name': folder_name,
            'mimeType': 'application/vnd.google-apps.folder'
        }
        if parent_id:
            file_metadata['parents'] = [parent_id]
        
        folder = service.files().create(body=file_metadata, fields='id').execute()
        folder_id = folder.get('id')
        
        # Cache the folder ID
        folder_cache[cache_key] = folder_id
        return folder_id


def check_file_exists(service, file_name, parent_id):
    """Check if a file with the given name already exists in the parent folder."""
    query = f"name = '{file_name}' and '{parent_id}' in parents and trashed = false"
    results = service.files().list(q=query, spaces='drive', fields='files(id, name)').execute()
    items = results.get('files', [])
    return items[0]['id'] if items else None


def upload_file(service, file_path, parent_id=None):
    """Upload a file to Google Drive."""
    file_name = os.path.basename(file_path)
    file_size = os.path.getsize(file_path)
    
    # Check if file already exists to prevent duplicates during retries
    existing_file_id = check_file_exists(service, file_name, parent_id)
    if existing_file_id:
        print(f"  File {file_name} already exists in destination (ID: {existing_file_id})")
        return existing_file_id
    
    # Set optimal chunk size based on file size
    if file_size > 100 * 1024 * 1024:  # > 100MB
        chunk_size = 10 * 1024 * 1024  # 10MB chunks
    elif file_size > 10 * 1024 * 1024:  # > 10MB
        chunk_size = 5 * 1024 * 1024   # 5MB chunks
    elif file_size < 1 * 1024 * 1024:  # < 1MB
        chunk_size = 256 * 1024        # 256KB chunks
    else:
        chunk_size = 1 * 1024 * 1024   # 1MB chunks
    
    # Create file metadata
    file_metadata = {
        'name': file_name,
    }
    if parent_id:
        file_metadata['parents'] = [parent_id]
    
    # Create media
    mimetype = mimetypes.guess_type(file_path)[0]
    if mimetype is None:
        mimetype = 'application/octet-stream'
    
    media = MediaFileUpload(
        file_path,
        mimetype=mimetype,
        chunksize=chunk_size,
        resumable=True
    )
    
    # Create and upload the file
    file = service.files().create(
        body=file_metadata,
        media_body=media,
        fields='id'
    )
    
    # Execute the upload with retry logic
    response = None
    max_retries = 5
    retry_count = 0
    
    while response is None and retry_count < max_retries:
        try:
            response = file.execute()
        except HttpError as error:
            if error.resp.status in [429, 500, 502, 503, 504]:
                # Rate limit or server error, retry with exponential backoff
                retry_count += 1
                wait_time = min(2 ** retry_count, 60)  # Exponential backoff, max 60 seconds
                print(f"  API error {error.resp.status}, retrying in {wait_time} seconds...")
                time.sleep(wait_time)
                
                # Check if file was actually created despite the error
                check_id = check_file_exists(service, file_name, parent_id)
                if check_id:
                    print(f"  File was actually created despite error (ID: {check_id})")
                    return check_id
                
                # Continue with retry
                continue
            else:
                # Other error, raise
                raise
    
    if response is None:
        raise Exception(f"Failed to upload file after {max_retries} retries")
    
    return response.get('id')


def batch_create_folders(service, folders, parent_id=None):
    """Create multiple folders in a batch request."""
    created_folders = {}
    
    # For small number of folders, create them one by one to avoid batch issues
    if len(folders) <= 5:
        for folder_name in folders:
            folder_id = find_or_create_folder(service, folder_name, parent_id)
            created_folders[folder_name] = folder_id
        return created_folders
    
    # Process in batches of 50 (API limit)
    batch_size = 50
    for i in range(0, len(folders), batch_size):
        batch_folders = folders[i:i+batch_size]
        
        # Create folders one by one for better error handling
        for folder_name in batch_folders:
            try:
                file_metadata = {
                    'name': folder_name,
                    'mimeType': 'application/vnd.google-apps.folder'
                }
                if parent_id:
                    file_metadata['parents'] = [parent_id]
                
                folder = service.files().create(body=file_metadata, fields='id').execute()
                created_folders[folder_name] = folder.get('id')
            except Exception as e:
                print(f"  Error creating folder {folder_name}: {str(e)}")
                # Fall back to find_or_create_folder for better reliability
                try:
                    folder_id = find_or_create_folder(service, folder_name, parent_id)
                    created_folders[folder_name] = folder_id
                except Exception as e2:
                    print(f"  Failed to create folder {folder_name}: {str(e2)}")
    
    return created_folders


def parallel_upload_files(file_items, parent_folder_ids, max_workers=5):
    """Upload multiple files in parallel."""
    results = {}
    
    def upload_file_worker(item):
        try:
            # Get the thread-local service
            service = get_service()
            
            # Get the parent folder ID
            parent_path = os.path.dirname(item['rel_path'])
            if not parent_path:
                parent_path = '.'
            
            parent_id = parent_folder_ids.get(parent_path)
            if not parent_id:
                return {
                    'success': False,
                    'error': f"Parent folder ID not found for {parent_path}",
                    'item': item
                }
            
            # Upload the file with duplicate prevention
            file_id = upload_file(service, item['path'], parent_id)
            
            return {
                'success': True,
                'id': file_id,
                'item': item
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'item': item
            }
    
    # Use ThreadPoolExecutor for parallel uploads
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all upload tasks
        future_to_item = {
            executor.submit(upload_file_worker, item): item['rel_path'] 
            for item in file_items
        }
        
        # Process results as they complete
        for future in concurrent.futures.as_completed(future_to_item):
            rel_path = future_to_item[future]
            try:
                result = future.result()
                results[rel_path] = result
            except Exception as e:
                results[rel_path] = {
                    'success': False,
                    'error': f"Exception during upload: {str(e)}",
                    'item': next(item for item in file_items if item['rel_path'] == rel_path)
                }
    
    return results
