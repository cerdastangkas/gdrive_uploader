#!/usr/bin/env python3
"""
Google Drive Folder Uploader - A tool to upload folders to Google Drive.
"""

__version__ = '0.2.0'

from gdrive_uploader.core.drive_api import authenticate
from gdrive_uploader.core.folder_uploader import upload_folder, is_folder_uploaded, record_folder_upload

def main():
    """Entry point for the command-line interface."""
    from gdrive_uploader.cli.upload_all import main as upload_all_main
    upload_all_main()