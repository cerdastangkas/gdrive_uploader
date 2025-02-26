#!/usr/bin/env python3
"""
Utility script to view and manage the uploaded folders CSV file.
"""

import os
import sys
import argparse
import pandas as pd
from tabulate import tabulate

# Path to the CSV file that tracks uploaded folders
UPLOADS_CSV = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', 'uploaded_folders.csv')

def list_uploads():
    """List all uploaded folders from the CSV file."""
    if not os.path.exists(UPLOADS_CSV):
        print("No uploads found. The CSV file does not exist yet.")
        return
    
    try:
        df = pd.read_csv(UPLOADS_CSV)
        if df.empty:
            print("No uploads found. The CSV file is empty.")
            return
        
        # Format the data for display
        display_df = df[['folder_name', 'folder_path', 'upload_time', 'drive_folder_id', 'uploaded']]
        print(tabulate(display_df, headers='keys', tablefmt='pretty', showindex=True))
        print(f"\nTotal uploads: {len(df)}")
    except Exception as e:
        print(f"Error reading CSV file: {e}")

def delete_upload(index):
    """Delete an upload entry from the CSV file by index."""
    if not os.path.exists(UPLOADS_CSV):
        print("No uploads found. The CSV file does not exist yet.")
        return
    
    try:
        df = pd.read_csv(UPLOADS_CSV)
        if df.empty:
            print("No uploads found. The CSV file is empty.")
            return
        
        if index < 0 or index >= len(df):
            print(f"Invalid index: {index}. Valid range is 0-{len(df)-1}.")
            return
        
        folder_name = df.iloc[index]['folder_name']
        folder_path = df.iloc[index]['folder_path']
        
        # Remove the row
        df = df.drop(index)
        
        # Save the updated DataFrame
        df.to_csv(UPLOADS_CSV, index=False)
        
        print(f"Deleted upload entry for folder: {folder_name} ({folder_path})")
    except Exception as e:
        print(f"Error updating CSV file: {e}")

def clear_uploads():
    """Clear all upload entries from the CSV file."""
    if not os.path.exists(UPLOADS_CSV):
        print("No uploads found. The CSV file does not exist yet.")
        return
    
    try:
        # Create an empty DataFrame with the same columns
        df = pd.read_csv(UPLOADS_CSV)
        columns = df.columns
        empty_df = pd.DataFrame(columns=columns)
        
        # Save the empty DataFrame
        empty_df.to_csv(UPLOADS_CSV, index=False)
        
        print(f"Cleared all upload entries ({len(df)} entries removed).")
    except Exception as e:
        print(f"Error clearing CSV file: {e}")

def main():
    """Main function to parse arguments and execute commands."""
    parser = argparse.ArgumentParser(description='Manage uploaded folders')
    subparsers = parser.add_subparsers(dest='command', help='Command to execute')
    
    # List command
    list_parser = subparsers.add_parser('list', help='List all uploaded folders')
    
    # Delete command
    delete_parser = subparsers.add_parser('delete', help='Delete an upload entry by index')
    delete_parser.add_argument('index', type=int, help='Index of the entry to delete')
    
    # Clear command
    clear_parser = subparsers.add_parser('clear', help='Clear all upload entries')
    
    args = parser.parse_args()
    
    if args.command == 'list' or not args.command:
        list_uploads()
    elif args.command == 'delete':
        delete_upload(args.index)
    elif args.command == 'clear':
        clear_uploads()
    else:
        parser.print_help()

if __name__ == '__main__':
    main()
