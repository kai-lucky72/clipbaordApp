#!/usr/bin/env python3
"""
Advanced Clipboard Manager - CLI Version

This is a command-line interface for the clipboard manager that allows
basic clipboard history management without requiring a GUI.
"""
import sys
import os
import logging
import json
import threading
import time
import argparse
import cmd
import hashlib
from datetime import datetime
from typing import Optional, Union, List

from database import DatabaseManager
from clipboard_manager import ClipboardManager, ClipItemType
from clipboard_adapter import ClipboardAdapter
from utils import setup_logger, limit_text_length, format_timestamp

# Configure logging
setup_logger()
logger = logging.getLogger(__name__)

class ClipboardManagerCLI(cmd.Cmd):
    """Command-line interface for the clipboard manager"""
    
    intro = """
    Advanced Clipboard Manager CLI
    Type 'help' to see available commands.
    """
    prompt = "clipboard> "
    
    def __init__(self):
        super().__init__()
        
        # Initialize database
        self.db_manager = DatabaseManager()
        logger.info("Database initialized")
        
        # In-memory clipboard for environments without system clipboard access
        self.in_memory_clipboard = None
        
        # Status flags
        self.monitoring = False
        self.monitor_thread = None
        
    def do_help(self, arg):
        """Show help message"""
        if arg:
            # Show help for specific command
            super().do_help(arg)
        else:
            # Show general help
            print("""
Available commands:

help            - Show this help message
start           - Start clipboard monitoring
stop            - Stop clipboard monitoring
recent [n]      - Show recent clipboard items (default 5)
search <text>   - Search clipboard history
add <text>      - Add text directly to clipboard history
copy <id>       - Copy item with ID to clipboard
favorite <id>   - Toggle favorite status for item
delete <id>     - Delete item from history
clear           - Clear clipboard history (keeps favorites)
exit            - Exit the application
            """)
    
    def do_start(self, arg):
        """Start clipboard monitoring"""
        if self.monitoring:
            print("Clipboard monitoring is already running.")
            return
        
        self.monitoring = True
        self.monitor_thread = threading.Thread(target=self._monitor_clipboard, daemon=True)
        self.monitor_thread.start()
        print("Clipboard monitoring started.")
    
    def do_stop(self, arg):
        """Stop clipboard monitoring"""
        if not self.monitoring:
            print("Clipboard monitoring is not running.")
            return
        
        self.monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=1.0)
        print("Clipboard monitoring stopped.")
    
    def do_recent(self, arg):
        """Show recent clipboard items"""
        try:
            limit = int(arg) if arg else 5
        except ValueError:
            limit = 5
        
        items = self.db_manager.get_recent_items(limit)
        if not items:
            print("No clipboard history available.")
            return
        
        print("\nRecent clipboard items:")
        print("-" * 60)
        for item in items:
            self._print_item(item)
        print("-" * 60)
    
    def do_search(self, arg):
        """Search clipboard history"""
        if not arg:
            print("Error: Please provide search text.")
            return
        
        items = self.db_manager.get_all_items(search_text=arg)
        if not items:
            print(f"No items found matching '{arg}'.")
            return
        
        print(f"\nSearch results for '{arg}':")
        print("-" * 60)
        for item in items:
            self._print_item(item)
        print("-" * 60)
    
    def do_add(self, arg):
        """Add text directly to clipboard history"""
        if not arg:
            print("Error: Please provide text to add.")
            return
        
        item_id = self.db_manager.add_clipboard_item(arg.encode('utf-8'), 'text')
        if item_id:
            print(f"Added to clipboard history with ID {item_id}")
            self.in_memory_clipboard = arg
        else:
            print("Failed to add item to clipboard history.")
    
    def do_copy(self, arg):
        """Copy item with ID to clipboard"""
        try:
            item_id = int(arg)
        except ValueError:
            print("Error: Please provide a valid item ID.")
            return
        
        item = self.db_manager.get_item_by_id(item_id)
        if not item:
            print(f"No item found with ID {item_id}.")
            return
            
        if not item['content']:
            print(f"Item with ID {item_id} has no content.")
            return
        
        if item['type'] == 'text':
            try:
                content = item['content'].decode('utf-8', errors='replace')
                self.in_memory_clipboard = content
                
                # Try to set system clipboard using our adapter
                if ClipboardAdapter.set_text(content):
                    print(f"Copied to system clipboard: {limit_text_length(content, 50)}")
                else:
                    logger.error("Failed to set clipboard content")
                    print(f"Copied to in-memory clipboard only: {limit_text_length(content, 50)}")
            except Exception as e:
                logger.error(f"Error decoding text content: {e}")
                print(f"Error copying content: {e}")
        else:
            print("Copying images to clipboard is not supported in CLI mode.")
    
    def do_favorite(self, arg):
        """Toggle favorite status for item"""
        try:
            item_id = int(arg)
        except ValueError:
            print("Error: Please provide a valid item ID.")
            return
        
        status = self.db_manager.toggle_favorite(item_id)
        if status is not None:
            state = "added to" if status else "removed from"
            print(f"Item {item_id} {state} favorites.")
        else:
            print(f"No item found with ID {item_id}.")
    
    def do_delete(self, arg):
        """Delete item from history"""
        try:
            item_id = int(arg)
        except ValueError:
            print("Error: Please provide a valid item ID.")
            return
        
        success = self.db_manager.delete_item(item_id)
        if success:
            print(f"Item {item_id} deleted from history.")
        else:
            print(f"No item found with ID {item_id}.")
    
    def do_clear(self, arg):
        """Clear clipboard history"""
        keep_favorites = True
        if arg and arg.lower() == 'all':
            keep_favorites = False
            print("Warning: This will clear ALL items including favorites.")
            confirm = input("Are you sure? (y/n): ")
            if confirm.lower() != 'y':
                print("Operation cancelled.")
                return
        
        count = self.db_manager.clear_history(keep_favorites)
        if keep_favorites:
            print(f"Cleared {count} non-favorite items from history.")
        else:
            print(f"Cleared all {count} items from history.")
    
    def do_exit(self, arg):
        """Exit the application"""
        if self.monitoring:
            self.do_stop(None)
        print("Exiting Clipboard Manager.")
        return True
    
    def _monitor_clipboard(self):
        """Background thread for monitoring clipboard changes"""
        try:
            # Implementation depends on the platform
            # For CLI, this is a simplified version
            logger.info("Starting clipboard monitoring using ClipboardAdapter")
            
            while self.monitoring:
                # Try to get clipboard content using our adapter
                try:
                    content = ClipboardAdapter.get_text()
                    if content and content != self.in_memory_clipboard:
                        self.in_memory_clipboard = content
                        self.db_manager.add_clipboard_item(content.encode('utf-8'), 'text')
                        logger.info("Clipboard content added to history")
                        
                    # Also check for images
                    image_data = ClipboardAdapter.get_image()
                    if image_data:
                        # Create a simple hash to avoid duplicates
                        image_hash = hashlib.md5(image_data).hexdigest()
                        item_id = self.db_manager.add_clipboard_item(image_data, 'image')
                        if item_id:
                            logger.info(f"Clipboard image added to history (ID: {item_id})")
                        
                except Exception as e:
                    logger.error(f"Error accessing clipboard: {e}")
                
                time.sleep(1)
        except Exception as e:
            logger.error(f"Error in clipboard monitoring: {e}")
            self.monitoring = False
    
    def _print_item(self, item):
        """Format and print a clipboard item"""
        if not item or 'id' not in item:
            print("[Unknown item]")
            return
            
        item_id = item['id']
        favorite = "★" if item.get('favorite', False) else " "
        timestamp = format_timestamp(item.get('timestamp', datetime.now()))
        
        if 'content' not in item or item['content'] is None:
            print(f"[{item_id}] {favorite} {timestamp}: [No content]")
            return
            
        if item['type'] == 'text':
            try:
                content = item['content'].decode('utf-8', errors='replace')
                content_preview = limit_text_length(content, 60)
                print(f"[{item_id}] {favorite} {timestamp}: {content_preview}")
            except Exception as e:
                logger.error(f"Error decoding text content: {e}")
                print(f"[{item_id}] {favorite} {timestamp}: [Error: {str(e)}]")
        else:
            print(f"[{item_id}] {favorite} {timestamp}: [IMAGE]")

def parse_arguments():
    """Parse command-line arguments"""
    parser = argparse.ArgumentParser(description="Advanced Clipboard Manager")
    parser.add_argument("--monitor", action="store_true", help="Start clipboard monitoring on startup")
    parser.add_argument("--recent", type=int, help="Display N most recent clipboard items and exit")
    return parser.parse_args()

def main():
    """Application entry point"""
    args = parse_arguments()
    
    # Simple mode: just show recent items and exit
    if args.recent:
        db_manager = DatabaseManager()
        items = db_manager.get_recent_items(args.recent)
        if not items:
            print("No clipboard history available.")
            return
        
        print("\nRecent clipboard items:")
        print("-" * 60)
        for item in items:
            if not item or 'id' not in item:
                print("[Unknown item]")
                continue
                
            item_id = item['id']
            favorite = "★" if item.get('favorite', False) else " "
            timestamp = format_timestamp(item.get('timestamp', datetime.now()))
            
            if 'content' not in item or item['content'] is None:
                print(f"[{item_id}] {favorite} {timestamp}: [No content]")
                continue
                
            if item['type'] == 'text':
                try:
                    content = item['content'].decode('utf-8', errors='replace')
                    content_preview = limit_text_length(content, 60)
                    print(f"[{item_id}] {favorite} {timestamp}: {content_preview}")
                except Exception as e:
                    logger.error(f"Error decoding text content: {e}")
                    print(f"[{item_id}] {favorite} {timestamp}: [Error: {str(e)}]")
            else:
                print(f"[{item_id}] {favorite} {timestamp}: [IMAGE]")
        print("-" * 60)
        return
    
    # Interactive mode
    try:
        cli = ClipboardManagerCLI()
        
        # Auto-start monitoring if requested
        if args.monitor:
            cli.do_start(None)
        
        # Start command loop
        cli.cmdloop()
    except KeyboardInterrupt:
        print("\nExiting Clipboard Manager.")
    except Exception as e:
        logger.error(f"Error in CLI application: {e}")
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
