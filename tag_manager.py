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
    Enhanced dialog for editing tags on a clipboard item
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
        self.dialog.geometry("500x400")
        self.dialog.transient(parent)  # Make it a modal dialog
        self.dialog.grab_set()  # Make it modal
        
        # Create custom styles for tag buttons
        self.create_styles()
        
        # Initialize UI
        self.create_ui()
        
    def create_styles(self):
        """Create custom styles for the tag editor"""
        style = ttk.Style()
        
        # Create style for tag buttons
        style.configure("Tag.TLabel", 
                       background="#e1e1e1", 
                       foreground="#333333",
                       padding=(8, 5),
                       font=("Helvetica", 9))
        
        # Create style for category tag buttons
        style.configure("CategoryTag.TLabel", 
                       background="#4a86e8", 
                       foreground="white",
                       padding=(8, 5),
                       font=("Helvetica", 9, "bold"))
        
        # Create style for remove button
        style.configure("RemoveTag.TButton", 
                       font=("Helvetica", 8),
                       padding=1)
                       
        # Create style for tag containers
        style.configure("TagContainer.TFrame", padding=5)
        
    def create_ui(self):
        """Create the dialog UI"""
        # Main frame with padding
        main_frame = ttk.Frame(self.dialog, padding="15")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Current tags section
        header_frame = ttk.Frame(main_frame)
        header_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(header_frame, text="Current Tags", font=("Helvetica", 12, "bold")).pack(side=tk.LEFT)
        
        # Create a scrollable canvas for the tags
        tag_canvas_frame = ttk.Frame(main_frame)
        tag_canvas_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 15))
        
        # Add canvas with scrollbar
        tag_canvas = tk.Canvas(tag_canvas_frame, highlightthickness=0)
        scrollbar = ttk.Scrollbar(tag_canvas_frame, orient=tk.VERTICAL, command=tag_canvas.yview)
        
        # Configure canvas
        tag_canvas.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        tag_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Create a frame inside the canvas for the tags
        self.tags_frame = ttk.Frame(tag_canvas, style="TagContainer.TFrame")
        tags_window = tag_canvas.create_window((0, 0), window=self.tags_frame, anchor="nw", tags="self.tags_frame")
        
        # Update scrollregion when the size of the frame changes
        def on_frame_configure(event):
            tag_canvas.configure(scrollregion=tag_canvas.bbox("all"))
            
        self.tags_frame.bind("<Configure>", on_frame_configure)
        
        # Make the canvas resize the window when the frame changes size
        def on_canvas_configure(event):
            tag_canvas.itemconfig(tags_window, width=event.width)
            
        tag_canvas.bind("<Configure>", on_canvas_configure)
        
        # Add current tags as buttons with X to remove
        self.update_tags_display()
        
        # Separator
        ttk.Separator(main_frame, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=15)
        
        # Add new tag section
        add_tag_frame = ttk.Frame(main_frame)
        add_tag_frame.pack(fill=tk.X, pady=(0, 15))
        
        ttk.Label(add_tag_frame, text="Add New Tag", font=("Helvetica", 12, "bold")).pack(anchor=tk.W)
        
        # Entry frame
        entry_frame = ttk.Frame(add_tag_frame)
        entry_frame.pack(fill=tk.X, pady=(5, 0))
        
        # Tag entry with autocomplete
        self.tag_var = tk.StringVar()
        self.tag_entry = ttk.Combobox(entry_frame, textvariable=self.tag_var)
        self.tag_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        
        # Populate with all tags for autocomplete
        self.tag_entry['values'] = self.all_tags
        
        # Add button
        add_button = ttk.Button(entry_frame, text="Add Tag", command=self.add_tag)
        add_button.pack(side=tk.RIGHT)
        
        # Bind enter key
        self.tag_entry.bind("<Return>", lambda e: self.add_tag())
        
        # Category section
        category_frame = ttk.Frame(main_frame)
        category_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(category_frame, text="Is this a category tag?").pack(side=tk.LEFT)
        
        # Category checkbox
        self.is_category = tk.BooleanVar(value=False)
        category_check = ttk.Checkbutton(category_frame, text="Yes", variable=self.is_category)
        category_check.pack(side=tk.LEFT, padx=(5, 0))
        
        # Existing tags section
        ttk.Label(main_frame, text="Existing Tags", font=("Helvetica", 12, "bold")).pack(anchor=tk.W, pady=(5, 5))
        
        # Create a frame with scrollbar for existing tags
        existing_tags_canvas_frame = ttk.Frame(main_frame)
        existing_tags_canvas_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # Add canvas with scrollbar
        existing_tags_canvas = tk.Canvas(existing_tags_canvas_frame, highlightthickness=0)
        existing_scrollbar = ttk.Scrollbar(existing_tags_canvas_frame, orient=tk.VERTICAL, command=existing_tags_canvas.yview)
        
        # Configure canvas
        existing_tags_canvas.configure(yscrollcommand=existing_scrollbar.set)
        existing_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        existing_tags_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Create a frame inside the canvas for the existing tags
        existing_tags_frame = ttk.Frame(existing_tags_canvas)
        existing_tags_window = existing_tags_canvas.create_window((0, 0), window=existing_tags_frame, anchor="nw")
        
        # Update scrollregion when the size of the frame changes
        existing_tags_frame.bind("<Configure>", lambda e: existing_tags_canvas.configure(scrollregion=existing_tags_canvas.bbox("all")))
        
        # Make the canvas resize the window when the frame changes size
        existing_tags_canvas.bind("<Configure>", lambda e: existing_tags_canvas.itemconfig(existing_tags_window, width=e.width))
        
        # Add buttons for existing tags if any
        if self.all_tags:
            row = 0
            col = 0
            max_cols = 4  # Maximum columns in grid
            
            for tag in sorted(self.all_tags):
                if tag not in self.current_tags:  # Only show tags that aren't already added
                    # Determine if this is a category tag (simplified check - could be stored in DB)
                    is_category = tag.startswith("#") or tag.startswith("@")
                    
                    # Create a tag button with appropriate style
                    tag_frame = ttk.Frame(existing_tags_frame)
                    
                    if is_category:
                        tag_button = ttk.Label(tag_frame, text=tag, style="CategoryTag.TLabel")
                    else:
                        tag_button = ttk.Label(tag_frame, text=tag, style="Tag.TLabel")
                    
                    tag_button.pack(side=tk.LEFT, padx=1, pady=1)
                    tag_button.bind("<Button-1>", lambda e, t=tag: self.add_existing_tag(t))
                    
                    tag_frame.grid(row=row, column=col, padx=2, pady=2, sticky=tk.W)
                    
                    col += 1
                    if col >= max_cols:
                        col = 0
                        row += 1
        else:
            ttk.Label(existing_tags_frame, text="No existing tags").grid(row=0, column=0, padx=10, pady=10)
        
        # Button frame at bottom
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, side=tk.BOTTOM, pady=(10, 0))
        
        # Close button
        close_button = ttk.Button(button_frame, text="Close", command=self.on_close)
        close_button.pack(side=tk.RIGHT)
    
    def update_tags_display(self):
        """Update the display of current tags"""
        # Clear existing tags
        for widget in self.tags_frame.winfo_children():
            widget.destroy()
        
        # Create a FlowFrame-like layout
        row = 0
        col = 0
        max_cols = 3  # Maximum columns in grid
        
        # Add current tags
        if not self.current_tags:
            no_tags_label = ttk.Label(self.tags_frame, text="No tags added yet")
            no_tags_label.grid(row=0, column=0, padx=10, pady=10, sticky=tk.W)
            return
        
        # Create a tag button for each current tag
        for tag in sorted(self.current_tags):
            # Create a container frame for the tag and its remove button
            tag_container = ttk.Frame(self.tags_frame)
            
            # Determine if this is a category tag (simplified check - could be stored in DB)
            is_category = tag.startswith("#") or tag.startswith("@")
            
            # Create a tag button with appropriate style
            if is_category:
                tag_button = ttk.Label(tag_container, text=tag, style="CategoryTag.TLabel")
            else:
                tag_button = ttk.Label(tag_container, text=tag, style="Tag.TLabel")
                
            tag_button.pack(side=tk.LEFT, padx=0, pady=0)
            
            # Add remove button
            remove_button = ttk.Button(
                tag_container,
                text="×",
                width=2,
                style="RemoveTag.TButton",
                command=lambda t=tag: self.remove_tag(t)
            )
            remove_button.pack(side=tk.RIGHT, padx=(2, 0))
            
            # Place the container in the grid
            tag_container.grid(row=row, column=col, padx=3, pady=3, sticky=tk.W)
            
            # Move to next column or row
            col += 1
            if col >= max_cols:
                col = 0
                row += 1
    
    def add_tag(self):
        """Add a new tag from the entry field"""
        tag = self.tag_var.get().strip()
        
        if not tag:
            return
            
        if tag in self.current_tags:
            messagebox.showinfo("Info", f"Tag '{tag}' already exists")
            return
        
        # Check if it should be a category tag
        if self.is_category.get() and not (tag.startswith("#") or tag.startswith("@")):
            tag = "#" + tag
        
        # Add the tag
        updated_tags = self.tag_manager.add_tag(self.item_id, tag)
        
        if updated_tags is not None:
            self.current_tags = updated_tags
            
            # Clear the entry
            self.tag_entry.delete(0, tk.END)
            
            # Update all tags list and refresh UI
            self.all_tags = self.tag_manager.get_all_tags()
            self.tag_entry['values'] = self.all_tags
            
            # Update tag display without recreating entire UI
            self.update_tags_display()
        else:
            messagebox.showerror("Error", f"Failed to add tag '{tag}'")
    
    def add_existing_tag(self, tag):
        """Add an existing tag"""
        if tag in self.current_tags:
            return
            
        # Add the tag
        updated_tags = self.tag_manager.add_tag(self.item_id, tag)
        
        if updated_tags is not None:
            self.current_tags = updated_tags
            
            # Update tag display without recreating entire UI
            self.update_tags_display()
    
    def remove_tag(self, tag):
        """Remove a tag"""
        # Remove the tag
        updated_tags = self.tag_manager.remove_tag(self.item_id, tag)
        
        if updated_tags is not None:
            self.current_tags = updated_tags
            
            # Update tag display without recreating entire UI
            self.update_tags_display()
    
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