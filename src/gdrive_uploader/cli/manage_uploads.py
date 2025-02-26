#!/usr/bin/env python3
"""
Command-line interface for managing uploaded folders.
"""

import os
import sys
import argparse
import pandas as pd
from tabulate import tabulate
from pathlib import Path

# Path to the CSV file that tracks uploaded folders
def get_uploads_csv_path():
    """Get the path to the uploads CSV file."""
    base_dir = Path(__file__).parent.parent.parent.parent.resolve()
    return os.path.join(base_dir, 'data', 'uploaded_folders.csv')

def list_uploads():
    """List all uploaded folders from the CSV file."""
    uploads_csv = get_uploads_csv_path()
    
    if not os.path.exists(uploads_csv):
        print("No uploads found. The CSV file does not exist yet.")
        return
    
    try:
        df = pd.read_csv(uploads_csv)
        
        if df.empty:
            print("No uploads found. The CSV file is empty.")
            return
        
        # Format the DataFrame for display
        display_df = df.copy()
        display_df['folder_hash'] = display_df['folder_hash'].str[:8] + '...'  # Truncate hash for display
        display_df.index = range(1, len(display_df) + 1)  # 1-based indexing for display
        
        print("\nUploaded Folders:")
        print(tabulate(display_df, headers='keys', tablefmt='psql'))
        print(f"\nTotal: {len(df)} folder(s)")
        
    except Exception as e:
        print(f"Error listing uploads: {e}")


def delete_upload(index):
    """Delete an upload entry from the CSV file by index."""
    uploads_csv = get_uploads_csv_path()
    
    if not os.path.exists(uploads_csv):
        print("No uploads found. The CSV file does not exist yet.")
        return
    
    try:
        df = pd.read_csv(uploads_csv)
        
        if df.empty:
            print("No uploads found. The CSV file is empty.")
            return
        
        # Check if the index is valid
        if index < 1 or index > len(df):
            print(f"Error: Invalid index. Please specify an index between 1 and {len(df)}.")
            return
        
        # Get the folder name to be deleted
        folder_name = df.iloc[index - 1]['folder_name']
        
        # Delete the row
        df = df.drop(index - 1)
        
        # Save the updated DataFrame to CSV
        df.to_csv(uploads_csv, index=False)
        
        print(f"Deleted upload entry for folder: {folder_name}")
        
    except Exception as e:
        print(f"Error deleting upload: {e}")


def clear_uploads():
    """Clear all upload entries from the CSV file."""
    uploads_csv = get_uploads_csv_path()
    
    if not os.path.exists(uploads_csv):
        print("No uploads found. The CSV file does not exist yet.")
        return
    
    try:
        df = pd.read_csv(uploads_csv)
        
        if df.empty:
            print("No uploads found. The CSV file is empty.")
            return
        
        # Get confirmation from the user
        confirm = input(f"Are you sure you want to clear all {len(df)} upload entries? (y/n): ")
        if confirm.lower() != 'y':
            print("Operation cancelled.")
            return
        
        # Create an empty DataFrame with the same columns
        empty_df = pd.DataFrame(columns=df.columns)
        
        # Save the empty DataFrame to CSV
        empty_df.to_csv(uploads_csv, index=False)
        
        print(f"Cleared all upload entries from the CSV file.")
        
    except Exception as e:
        print(f"Error clearing uploads: {e}")


def main():
    """Main function to parse arguments and execute commands."""
    parser = argparse.ArgumentParser(
        description='Manage uploaded folders'
    )
    subparsers = parser.add_subparsers(dest='command', help='Command to execute')
    
    # List command
    list_parser = subparsers.add_parser('list', help='List all uploaded folders')
    
    # Delete command
    delete_parser = subparsers.add_parser('delete', help='Delete an upload entry by index')
    delete_parser.add_argument('index', type=int, help='Index of the upload entry to delete')
    
    # Clear command
    clear_parser = subparsers.add_parser('clear', help='Clear all upload entries')
    
    args = parser.parse_args()
    
    if args.command == 'list':
        list_uploads()
    elif args.command == 'delete':
        delete_upload(args.index)
    elif args.command == 'clear':
        clear_uploads()
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
