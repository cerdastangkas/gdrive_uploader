#!/usr/bin/env python3
"""
Main entry point for the Google Drive Folder Uploader CLI.
"""

import os
import sys
import argparse
from pathlib import Path

# Add the src directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'src'))

from gdrive_uploader.cli.upload_all import main as upload_all_main
from gdrive_uploader.cli.add_folder import main as add_folder_main
from gdrive_uploader.cli.manage_uploads import main as manage_uploads_main

def main():
    """Main function to parse arguments and dispatch to the appropriate command."""
    parser = argparse.ArgumentParser(
        description='Google Drive Folder Uploader - A tool to upload folders to Google Drive'
    )
    subparsers = parser.add_subparsers(dest='command', help='Command to execute')
    
    # Upload all command
    upload_parser = subparsers.add_parser('upload-all', help='Upload all folders in the to_upload directory')
    upload_parser.add_argument(
        '--parent-id', 
        help='ID of the parent folder in Google Drive (optional)'
    )
    upload_parser.add_argument(
        '--force', 
        action='store_true', 
        help='Force upload even if folders have been uploaded before'
    )
    upload_parser.add_argument(
        '--timeout',
        type=int,
        help='Maximum time in minutes to allow the upload process to run'
    )
    upload_parser.add_argument(
        '--workers',
        type=int,
        default=5,
        help='Number of parallel upload workers (default: 5)'
    )
    upload_parser.add_argument(
        '--batch-size',
        type=int,
        default=100,
        help='Batch size for file uploads (default: 100)'
    )
    
    # Add folder command
    add_parser = subparsers.add_parser('add-folder', help='Add a folder to the to_upload directory')
    add_parser.add_argument(
        'folder_path',
        help='Path to the folder to add'
    )
    add_parser.add_argument(
        '--move',
        action='store_true',
        help='Move the folder instead of copying it'
    )
    
    # Manage uploads command
    manage_parser = subparsers.add_parser('manage', help='Manage uploaded folders')
    manage_subparsers = manage_parser.add_subparsers(dest='manage_command', help='Manage command to execute')
    
    # List command
    list_parser = manage_subparsers.add_parser('list', help='List all uploaded folders')
    
    # Delete command
    delete_parser = manage_subparsers.add_parser('delete', help='Delete an upload entry by index')
    delete_parser.add_argument('index', type=int, help='Index of the upload entry to delete')
    
    # Clear command
    clear_parser = manage_subparsers.add_parser('clear', help='Clear all upload entries')
    
    args = parser.parse_args()
    
    if args.command == 'upload-all':
        # Remove the command from sys.argv and call the upload_all_main function
        sys.argv = [sys.argv[0]] + sys.argv[2:]
        upload_all_main()
    elif args.command == 'add-folder':
        # Remove the command from sys.argv and call the add_folder_main function
        sys.argv = [sys.argv[0]] + sys.argv[2:]
        add_folder_main()
    elif args.command == 'manage':
        # Remove the command from sys.argv and call the manage_uploads_main function
        if args.manage_command:
            sys.argv = [sys.argv[0]] + sys.argv[3:]
        else:
            sys.argv = [sys.argv[0]]
        manage_uploads_main()
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
