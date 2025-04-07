#!/usr/bin/env python3
"""
Tag Manager Module

This module handles tagging functionality for clipboard items.
"""
import tkinter as tk
from tkinter import ttk, messagebox
import logging
import json
from typing import List, Dict, Any

# Configure logging
logger = logging.getLogger(__name__)

class TagManager:
    """
    Manages tags for clipboard items
    """
    def __init__(self, db_manager):
        """
        Initialize the tag manager
        
        Args:
            db_manager: Database manager instance
        """
        self.db_manager = db_manager
        
    def get_item_tags(self, item_id: int) -> List[str]:
        """
        Get tags for a specific item
        
        Args:
            item_id: The ID of the item to get tags for
            
        Returns:
            List of tags
        """
        item = self.db_manager.get_item_by_id(item_id)
        if not item or 'tags' not in item:
            return []
        
        try:
            # Tags are stored as a JSON string
            if item['tags']:
                return json.loads(item['tags'])
        except Exception as e:
            logger.error(f"Error parsing tags for item {item_id}: {e}")
        
        return []
        
    def add_tag(self, item_id: int, tag: str) -> List[str]:
        """
        Add a tag to an item
        
        Args:
            item_id: The ID of the item to tag
            tag: The tag to add
            
        Returns:
            Updated list of tags or None if failed
        """
        return self.db_manager.add_tag(item_id, tag)
        
    def remove_tag(self, item_id: int, tag: str) -> List[str]:
        """
        Remove a tag from an item
        
        Args:
            item_id: The ID of the item
            tag: The tag to remove
            
        Returns:
            Updated list of tags or None if failed
        """
        return self.db_manager.remove_tag(item_id, tag)
    
    def get_all_tags(self) -> List[str]:
        """
        Get all unique tags used in the database
        
        Returns:
            List of unique tags
        """
        all_items = self.db_manager.get_all_items()
        all_tags = set()
        
        for item in all_items:
            if 'tags' in item and item['tags']:
                try:
                    tags = json.loads(item['tags'])
                    all_tags.update(tags)
                except Exception as e:
                    logger.error(f"Error parsing tags: {e}")
        
        return sorted(list(all_tags))
    
    def get_items_by_tag(self, tag: str) -> List[Dict[str, Any]]:
        """
        Get all items with a specific tag
        
        Args:
            tag: The tag to filter by
            
        Returns:
            List of clipboard items with the specified tag
        """
        all_items = self.db_manager.get_all_items()
        filtered_items = []
        
        for item in all_items:
            if 'tags' in item and item['tags']:
                try:
                    tags = json.loads(item['tags'])
                    if tag in tags:
                        filtered_items.append(item)
                except Exception as e:
                    logger.error(f"Error parsing tags: {e}")
        
        return filtered_items


class TagEditorDialog:
    """
    Dialog for editing tags on a clipboard item
    """
    def __init__(self, parent, item_id, tag_manager):
        """
        Initialize the tag editor dialog
        
        Args:
            parent: Parent widget
            item_id: ID of the clipboard item to edit
            tag_manager: TagManager instance
        """
        self.parent = parent
        self.item_id = item_id
        self.tag_manager = tag_manager
        self.current_tags = tag_manager.get_item_tags(item_id)
        self.all_tags = tag_manager.get_all_tags()
        
        # Create dialog window
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Edit Tags")
        self.dialog.geometry("400x300")
        self.dialog.transient(parent)  # Make it a modal dialog
        self.dialog.grab_set()  # Make it modal
        
        # Initialize UI
        self.create_ui()
        
    def create_ui(self):
        """Create the dialog UI"""
        # Main frame with padding
        main_frame = ttk.Frame(self.dialog, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Current tags section
        ttk.Label(main_frame, text="Current Tags:", font=("Helvetica", 10, "bold")).pack(anchor=tk.W, pady=(0, 5))
        
        # Tags frame
        tags_frame = ttk.Frame(main_frame)
        tags_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Add current tags as buttons with X to remove
        self.update_tags_display(tags_frame)
        
        # Separator
        ttk.Separator(main_frame, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=10)
        
        # Add new tag section
        ttk.Label(main_frame, text="Add New Tag:", font=("Helvetica", 10, "bold")).pack(anchor=tk.W, pady=(0, 5))
        
        # Entry frame
        entry_frame = ttk.Frame(main_frame)
        entry_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Tag entry
        self.tag_entry = ttk.Entry(entry_frame)
        self.tag_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        
        # Add button
        add_button = ttk.Button(entry_frame, text="Add", command=self.add_tag)
        add_button.pack(side=tk.RIGHT)
        
        # Bind enter key
        self.tag_entry.bind("<Return>", lambda e: self.add_tag())
        
        # Existing tags section if any
        if self.all_tags:
            ttk.Label(main_frame, text="Existing Tags:", font=("Helvetica", 10, "bold")).pack(anchor=tk.W, pady=(10, 5))
            
            # Create a frame for existing tags
            existing_tags_frame = ttk.Frame(main_frame)
            existing_tags_frame.pack(fill=tk.X)
            
            # Add buttons for existing tags
            row = 0
            col = 0
            for tag in self.all_tags:
                if tag not in self.current_tags:  # Only show tags that aren't already added
                    tag_button = ttk.Button(
                        existing_tags_frame, 
                        text=tag,
                        command=lambda t=tag: self.add_existing_tag(t)
                    )
                    tag_button.grid(row=row, column=col, padx=2, pady=2, sticky=tk.W)
                    
                    col += 1
                    if col > 3:
                        col = 0
                        row += 1
        
        # Button frame at bottom
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, side=tk.BOTTOM, pady=(10, 0))
        
        # Close button
        close_button = ttk.Button(button_frame, text="Close", command=self.on_close)
        close_button.pack(side=tk.RIGHT)
    
    def update_tags_display(self, parent_frame):
        """Update the display of current tags"""
        # Clear existing tags
        for widget in parent_frame.winfo_children():
            widget.destroy()
        
        # Add current tags
        if not self.current_tags:
            no_tags_label = ttk.Label(parent_frame, text="No tags")
            no_tags_label.pack(anchor=tk.W)
            return
        
        # Create a tag for each current tag
        for i, tag in enumerate(self.current_tags):
            tag_frame = ttk.Frame(parent_frame)
            tag_frame.pack(side=tk.LEFT, padx=2, pady=2)
            
            # Create a styled frame for the tag
            tag_label = ttk.Label(tag_frame, text=tag, padding=(5, 2))
            tag_label.pack(side=tk.LEFT)
            
            # Add remove button
            remove_button = ttk.Button(
                tag_frame,
                text="×",
                width=2,
                command=lambda t=tag: self.remove_tag(t)
            )
            remove_button.pack(side=tk.RIGHT)
    
    def add_tag(self):
        """Add a new tag from the entry field"""
        tag = self.tag_entry.get().strip()
        
        if not tag:
            return
            
        if tag in self.current_tags:
            messagebox.showinfo("Info", f"Tag '{tag}' already exists")
            return
            
        # Add the tag
        updated_tags = self.tag_manager.add_tag(self.item_id, tag)
        
        if updated_tags is not None:
            self.current_tags = updated_tags
            
            # Update the display
            self.update_tags_display(self.dialog.winfo_children()[0].winfo_children()[1])
            
            # Clear the entry
            self.tag_entry.delete(0, tk.END)
            
            # Refresh dialog (recreate UI to show updated existing tags)
            self.all_tags = self.tag_manager.get_all_tags()
            for widget in self.dialog.winfo_children():
                widget.destroy()
            self.create_ui()
    
    def add_existing_tag(self, tag):
        """Add an existing tag"""
        if tag in self.current_tags:
            return
            
        # Add the tag
        updated_tags = self.tag_manager.add_tag(self.item_id, tag)
        
        if updated_tags is not None:
            self.current_tags = updated_tags
            
            # Refresh dialog (recreate UI)
            for widget in self.dialog.winfo_children():
                widget.destroy()
            self.create_ui()
    
    def remove_tag(self, tag):
        """Remove a tag"""
        # Remove the tag
        updated_tags = self.tag_manager.remove_tag(self.item_id, tag)
        
        if updated_tags is not None:
            self.current_tags = updated_tags
            
            # Refresh dialog (recreate UI)
            for widget in self.dialog.winfo_children():
                widget.destroy()
            self.create_ui()
    
    def on_close(self):
        """Close the dialog"""
        self.dialog.destroy()


def main():
    """Test function"""
    from database import DatabaseManager
    
    root = tk.Tk()
    root.title("Tag Editor Test")
    root.geometry("500x400")
    
    db_manager = DatabaseManager()
    tag_manager = TagManager(db_manager)
    
    def open_dialog():
        # Use the first item in the database for testing
        items = db_manager.get_recent_items(1)
        if items:
            TagEditorDialog(root, items[0]['id'], tag_manager)
        else:
            messagebox.showinfo("Info", "No items in database")
    
    open_button = ttk.Button(root, text="Open Tag Editor", command=open_dialog)
    open_button.pack(pady=20)
    
    root.mainloop()

if __name__ == "__main__":
    main()