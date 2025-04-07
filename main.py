#!/usr/bin/env python3
"""
Advanced Clipboard Manager - CLI Version

This is a command-line interface for the clipboard manager that works in environments
where GUI applications are not supported.
"""
import sys
import os
import logging
import argparse
import time
import json
import subprocess
from datetime import datetime
import threading

from database import DatabaseManager
from utils import setup_logger, limit_text_length, format_timestamp

# In-memory clipboard for environments without system clipboard access
_MEMORY_CLIPBOARD = ""

# Clipboard utilities using system commands if available, otherwise use in-memory clipboard
def clipboard_copy(text):
    """Copy text to clipboard using system commands or in-memory fallback"""
    global _MEMORY_CLIPBOARD
    try:
        if sys.platform == 'darwin':  # macOS
            subprocess.run('pbcopy', universal_newlines=True, input=text)
        elif sys.platform == 'win32':  # Windows
            subprocess.run(['clip'], universal_newlines=True, input=text)
        else:  # Linux/Unix
            try:
                subprocess.run(['xclip', '-selection', 'clipboard'], universal_newlines=True, input=text)
            except FileNotFoundError:
                # Fallback to in-memory clipboard in Replit environment
                _MEMORY_CLIPBOARD = text
                return True
        return True
    except Exception as e:
        # Fallback to in-memory clipboard
        _MEMORY_CLIPBOARD = text
        logging.warning(f"Using in-memory clipboard: {e}")
        return True

def clipboard_paste():
    """Paste from clipboard using system commands or in-memory fallback"""
    global _MEMORY_CLIPBOARD
    try:
        if sys.platform == 'darwin':  # macOS
            return subprocess.check_output('pbpaste', universal_newlines=True)
        elif sys.platform == 'win32':  # Windows
            # Using PowerShell to get clipboard contents
            return subprocess.check_output(['powershell.exe', '-command', 'Get-Clipboard'], 
                                          universal_newlines=True)
        else:  # Linux/Unix
            try:
                return subprocess.check_output(['xclip', '-selection', 'clipboard', '-o'],
                                              universal_newlines=True)
            except FileNotFoundError:
                # Fallback to in-memory clipboard in Replit environment
                return _MEMORY_CLIPBOARD
    except Exception as e:
        # Fallback to in-memory clipboard
        logging.warning(f"Using in-memory clipboard: {e}")
        return _MEMORY_CLIPBOARD

# Configure logging
setup_logger()
logger = logging.getLogger(__name__)

class CliClipboardManager:
    """A CLI-based clipboard manager"""
    
    def __init__(self, db_manager):
        self.db_manager = db_manager
        self.last_clipboard_content = ""
        self.monitoring = False
        self.monitor_thread = None
        logger.info("CLI Clipboard Manager initialized")
    
    def start_monitoring(self):
        """Start clipboard monitoring"""
        if self.monitoring:
            print("Clipboard monitoring is already running.")
            return
        
        self.monitoring = True
        self.monitor_thread = threading.Thread(target=self._monitor_clipboard)
        self.monitor_thread.daemon = True
        self.monitor_thread.start()
        print("Clipboard monitoring started. Press Ctrl+C to stop.")
    
    def stop_monitoring(self):
        """Stop clipboard monitoring"""
        self.monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=1.0)
        print("Clipboard monitoring stopped.")
    
    def _monitor_clipboard(self):
        """Monitor clipboard for changes"""
        try:
            while self.monitoring:
                current_content = clipboard_paste()
                
                # Check if content has changed
                if current_content != self.last_clipboard_content and current_content:
                    self.last_clipboard_content = current_content
                    # Store in database
                    self.db_manager.add_clipboard_item(
                        content=current_content, 
                        item_type="text"
                    )
                    logger.info(f"New clipboard content saved: {limit_text_length(current_content, 30)}")
                    print(f"\nNew clipboard content saved: {limit_text_length(current_content, 30)}")
                
                # Sleep to avoid high CPU usage
                time.sleep(1.0)
        except Exception as e:
            logger.error(f"Error in clipboard monitoring: {e}")
            print(f"Error: {e}")
    
    def display_recent_items(self, count=5):
        """Display the most recent clipboard items"""
        items = self.db_manager.get_recent_items(limit=count)
        
        if not items:
            print("No clipboard history found.")
            return
        
        print("\n=== Recent Clipboard Items ===")
        for idx, item in enumerate(items):
            timestamp = format_timestamp(item['timestamp'])
            content = limit_text_length(item['content'].decode('utf-8', 'replace') if isinstance(item['content'], bytes) else item['content'], 60)
            star = "★" if item['favorite'] else " "
            print(f"{idx+1}. [{star}] {content} - {timestamp}")
    
    def copy_item_to_clipboard(self, item_id):
        """Copy an item from history to clipboard"""
        item = self.db_manager.get_item_by_id(item_id)
        
        if not item:
            print(f"No item found with ID {item_id}")
            return
        
        content = item['content']
        if isinstance(content, bytes):
            try:
                content = content.decode('utf-8')
            except UnicodeDecodeError:
                print("Cannot copy binary data to clipboard in CLI mode")
                return
        
        clipboard_copy(content)
        print(f"Copied item to clipboard: {limit_text_length(content, 30)}")
    
    def toggle_favorite(self, item_id):
        """Toggle favorite status for an item"""
        result = self.db_manager.toggle_favorite(item_id)
        if result is not None:
            status = "added to" if result else "removed from"
            print(f"Item {status} favorites")
        else:
            print(f"No item found with ID {item_id}")
    
    def delete_item(self, item_id):
        """Delete an item from history"""
        if self.db_manager.delete_item(item_id):
            print(f"Deleted item {item_id}")
        else:
            print(f"No item found with ID {item_id}")
    
    def search_items(self, search_text):
        """Search for items in clipboard history"""
        items = self.db_manager.get_all_items(search_text=search_text)
        
        if not items:
            print(f"No items found matching '{search_text}'")
            return
        
        print(f"\n=== Search Results for '{search_text}' ===")
        for item in items:
            timestamp = format_timestamp(item['timestamp'])
            content = limit_text_length(item['content'].decode('utf-8', 'replace') if isinstance(item['content'], bytes) else item['content'], 60)
            star = "★" if item['favorite'] else " "
            print(f"ID {item['id']}: [{star}] {content} - {timestamp}")
            
    def add_manual_item(self, content):
        """Manually add content to clipboard history"""
        if not content:
            print("Cannot add empty content")
            return
            
        # Add to clipboard memory
        clipboard_copy(content)
        
        # Store in database
        item_id = self.db_manager.add_clipboard_item(
            content=content,
            item_type="text"
        )
        
        print(f"Added to clipboard history with ID {item_id}")
        return item_id

def interactive_mode(clipboard_manager):
    """Run the clipboard manager in interactive mode"""
    print("\nWelcome to Advanced Clipboard Manager (CLI Edition)")
    print("Type 'help' to see available commands\n")
    
    while True:
        try:
            command = input("\nclipboard> ").strip().lower()
            
            if command == "help":
                print("\nAvailable commands:")
                print("  start       - Start clipboard monitoring")
                print("  stop        - Stop clipboard monitoring")
                print("  recent [n]  - Show recent clipboard items (default 5)")
                print("  search <text> - Search clipboard history")
                print("  add <text>  - Add text directly to clipboard history")
                print("  copy <id>   - Copy item with ID to clipboard")
                print("  favorite <id> - Toggle favorite status for item")
                print("  delete <id> - Delete item from history")
                print("  clear       - Clear clipboard history (keeps favorites)")
                print("  exit        - Exit the application")
            
            elif command == "start":
                clipboard_manager.start_monitoring()
            
            elif command == "stop":
                clipboard_manager.stop_monitoring()
            
            elif command.startswith("recent"):
                parts = command.split()
                count = 5  # default
                if len(parts) > 1 and parts[1].isdigit():
                    count = int(parts[1])
                clipboard_manager.display_recent_items(count)
            
            elif command.startswith("search "):
                search_text = command[7:]
                if search_text:
                    clipboard_manager.search_items(search_text)
                else:
                    print("Please provide search text")
                    
            elif command.startswith("add "):
                text = command[4:]
                if text:
                    clipboard_manager.add_manual_item(text)
                else:
                    print("Please provide text to add")
            
            elif command.startswith("copy "):
                parts = command.split()
                if len(parts) == 2 and parts[1].isdigit():
                    clipboard_manager.copy_item_to_clipboard(int(parts[1]))
                else:
                    print("Usage: copy <id>")
            
            elif command.startswith("favorite "):
                parts = command.split()
                if len(parts) == 2 and parts[1].isdigit():
                    clipboard_manager.toggle_favorite(int(parts[1]))
                else:
                    print("Usage: favorite <id>")
            
            elif command.startswith("delete "):
                parts = command.split()
                if len(parts) == 2 and parts[1].isdigit():
                    clipboard_manager.delete_item(int(parts[1]))
                else:
                    print("Usage: delete <id>")
            
            elif command == "clear":
                confirm = input("Clear clipboard history? (y/n): ").lower()
                if confirm == 'y':
                    count = clipboard_manager.db_manager.clear_history(keep_favorites=True)
                    print(f"Cleared {count} items from history (favorites preserved)")
            
            elif command in ["exit", "quit"]:
                clipboard_manager.stop_monitoring()
                print("Exiting Advanced Clipboard Manager")
                break
            
            else:
                print("Unknown command. Type 'help' to see available commands.")
                
        except KeyboardInterrupt:
            print("\nInterrupted by user")
            clipboard_manager.stop_monitoring()
            break
        except Exception as e:
            logger.error(f"Error: {e}")
            print(f"Error: {e}")

def main():
    parser = argparse.ArgumentParser(description="Advanced Clipboard Manager - CLI Edition")
    parser.add_argument("--monitor", action="store_true", help="Start clipboard monitoring on startup")
    parser.add_argument("--recent", type=int, help="Display recent clipboard items and exit")
    
    args = parser.parse_args()
    
    # Initialize database manager
    db_manager = DatabaseManager()
    
    # Initialize clipboard manager
    clipboard_manager = CliClipboardManager(db_manager)
    
    # Handle command line options
    if args.recent:
        clipboard_manager.display_recent_items(args.recent)
        return
    
    if args.monitor:
        clipboard_manager.start_monitoring()
    
    # Enter interactive mode
    try:
        interactive_mode(clipboard_manager)
    except Exception as e:
        logger.error(f"Error in interactive mode: {e}")
        print(f"Error: {e}")
    finally:
        # Ensure monitoring is stopped
        clipboard_manager.stop_monitoring()

if __name__ == "__main__":
    main()
