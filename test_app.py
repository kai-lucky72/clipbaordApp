#!/usr/bin/env python
"""
Test script for the Advanced Clipboard Manager CLI
"""
import os
import subprocess
import time
import logging

def run_test():
    """Run a test of the clipboard manager functionality"""
    # Test the recent items command
    print("\n--- Testing 'recent' command ---")
    result = subprocess.run(["python", "main.py", "--recent", "3"], 
                          capture_output=True, text=True)
    print(result.stdout)
    
    # Test adding a manual item using the add_manual_item function
    print("\n--- Testing database direct access ---")
    from database import DatabaseManager
    
    db = DatabaseManager()
    test_item = "Test item added programmatically " + time.strftime("%H:%M:%S")
    item_id = db.add_clipboard_item(test_item, "text")
    print(f"Added item with ID: {item_id}")
    
    # Get recent items
    recent = db.get_recent_items(2)
    print("\nRecent items:")
    for item in recent:
        content = item['content'].decode('utf-8') if isinstance(item['content'], bytes) else item['content']
        favorite = "★" if item['favorite'] else " "
        print(f"[{favorite}] {item['id']}: {content[:30]}")
    
    # Toggle favorite status
    if recent and len(recent) > 0:
        toggle_id = recent[0]['id']
        new_status = db.toggle_favorite(toggle_id)
        print(f"\nToggled favorite status for item {toggle_id}: {'Favorite' if new_status else 'Not favorite'}")
    
    # Test search
    print("\n--- Testing search ---")
    search_results = db.get_all_items(search_text="test")
    print(f"Found {len(search_results)} items matching 'test':")
    for item in search_results:
        content = item['content'].decode('utf-8') if isinstance(item['content'], bytes) else item['content']
        favorite = "★" if item['favorite'] else " "
        print(f"[{favorite}] {item['id']}: {content[:30]}")
    
    print("\nTest completed successfully!")

if __name__ == "__main__":
    run_test()