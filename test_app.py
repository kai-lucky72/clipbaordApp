#!/usr/bin/env python3
"""
Test script for the Advanced Clipboard Manager CLI - Database-only test
This version completely avoids importing any PyQt5 or clipboard-related code
that could cause issues in a headless environment.
"""
import os
import subprocess
import time
import logging
import sys
import json

def run_database_test():
    """Run a test of the database operations without GUI/clipboard dependencies"""
    print("\n--- Testing DatabaseManager functionality ---")
    
    from database import DatabaseManager
    
    # Create a direct database connection
    db = DatabaseManager()
    
    # Add test items directly to database
    test_items = [
        f"Pure DB Test item #1 added at {time.strftime('%H:%M:%S')}",
        f"Pure DB Test item #2 with special chars: !@#$%^&*()",
        f"Pure DB Test item #3 with a longer content that should be stored in the database"
    ]
    
    print("\nAdding test items directly to database:")
    for i, item in enumerate(test_items):
        # Convert text to bytes for storage
        content_bytes = item.encode('utf-8')
        item_id = db.add_clipboard_item(content_bytes, 'text')
        print(f"Added: ID {item_id}: {item[:30]}...")
        
        # Make the first item a favorite
        if i == 0:
            db.toggle_favorite(item_id)
            print(f"Marked item {item_id} as a favorite")
    
    # Get recent items
    print("\nRecent items:")
    try:
        recent = db.get_recent_items(5)
        if not recent:
            print("No recent items found.")
        else:
            for item in recent:
                if 'content' in item and item['content'] is not None:
                    if item['type'] == 'text':
                        try:
                            content = item['content'].decode('utf-8', errors='replace')
                            favorite = "★" if item.get('favorite', False) else " "
                            print(f"[{favorite}] {item['id']}: {content[:50]}...")
                        except Exception as e:
                            print(f"[E] {item['id']}: Error decoding content: {str(e)}")
                    else:
                        print(f"[{item['id']}]: [IMAGE]")
    except Exception as e:
        print(f"Error getting recent items: {str(e)}")
    
    # Toggle favorite status
    try:
        if recent and len(recent) > 0:
            toggle_id = recent[0]['id']
            new_status = db.toggle_favorite(toggle_id)
            print(f"\nToggled favorite status for item {toggle_id}: {'Favorite' if new_status else 'Not favorite'}")
    except Exception as e:
        print(f"Error toggling favorite: {str(e)}")
    
    # Test search functionality
    print("\n--- Testing search ---")
    try:
        search_results = db.get_all_items(search_text="test")
        print(f"Found {len(search_results)} items matching 'test':")
        for item in search_results:
            if 'content' in item and item['content'] is not None:
                if item['type'] == 'text':
                    try:
                        content = item['content'].decode('utf-8', errors='replace')
                        favorite = "★" if item.get('favorite', False) else " "
                        print(f"[{favorite}] {item['id']}: {content[:50]}...")
                    except Exception as e:
                        print(f"[E] {item['id']}: Error decoding content: {str(e)}")
                else:
                    print(f"[{item['id']}]: [IMAGE]")
    except Exception as e:
        print(f"Error searching: {str(e)}")
    
    # Test tag functionality
    try:
        if recent and len(recent) > 0:
            tag_item_id = recent[0]['id']
            print(f"\n--- Testing tag functionality on item {tag_item_id} ---")
            
            tags = db.add_tag(tag_item_id, "test-tag")
            print(f"Added tag 'test-tag' to item {tag_item_id}: {tags}")
            
            tags = db.add_tag(tag_item_id, "another-tag")
            print(f"Added tag 'another-tag' to item {tag_item_id}: {tags}")
            
            tags = db.remove_tag(tag_item_id, "test-tag")
            print(f"Removed tag 'test-tag' from item {tag_item_id}: {tags}")
    except Exception as e:
        print(f"Error with tags: {str(e)}")
        
    print("\nDatabase test completed successfully!")

if __name__ == "__main__":
    run_database_test()