#!/usr/bin/env python3
"""
Quick Paste Popup Module

This module implements a quick paste popup that shows recent clipboard items
when triggered by a keyboard shortcut.
"""
import os
import sys
import logging
import tkinter as tk
from tkinter import ttk
from io import BytesIO
from PIL import Image, ImageTk
import threading
import time

from database import DatabaseManager
from clipboard_adapter import ClipboardAdapter
from clipboard_manager import ClipItemType
from utils import setup_logger, limit_text_length, format_timestamp

# Configure logging
setup_logger()
logger = logging.getLogger(__name__)

class KeyboardListener(threading.Thread):
    """
    Thread to monitor keyboard for the Ctrl+Shift+V shortcut
    using platform-specific methods
    """
    def __init__(self, callback):
        """Initialize the keyboard listener"""
        super().__init__(daemon=True)
        self.callback = callback
        self.running = True
        self.last_keypress_time = time.time()
        
    def run(self):
        """Monitor for keyboard shortcuts"""
        try:
            # Try to use platform-specific keyboard monitoring
            # For simplicity in this implementation, we'll use polling
            # with the tkinter event system instead of a low-level keyboard hook
            logger.info("Keyboard listener started")
            
            while self.running:
                time.sleep(0.1)
                
        except Exception as e:
            logger.error(f"Error in keyboard listener: {e}")
            
    def stop(self):
        """Stop the keyboard listener"""
        self.running = False

class QuickPastePopup:
    """
    Quick paste popup that shows recent clipboard items
    """
    def __init__(self, parent=None):
        """Initialize the quick paste popup"""
        self.parent = parent
        
        # Initialize database
        self.db_manager = DatabaseManager()
        
        # Create the popup window - initially hidden
        self.create_popup_window()
        
        # Start the keyboard listener
        self.keyboard_listener = None
        
    def create_popup_window(self):
        """Create the popup window"""
        # Create popup window - initially hidden
        self.popup = tk.Toplevel(self.parent) if self.parent else tk.Toplevel()
        self.popup.title("Quick Paste")
        self.popup.geometry("400x300")
        self.popup.attributes("-topmost", True)  # Keep on top
        self.popup.withdraw()  # Hide initially
        
        # Style
        style = ttk.Style()
        style.configure("Popup.TFrame", background="#F0F0F0")
        
        # Main frame
        self.main_frame = ttk.Frame(self.popup, style="Popup.TFrame", padding=10)
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Title label
        title_frame = ttk.Frame(self.main_frame)
        title_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(title_frame, text="Recent Clipboard Items", font=('Arial', 12, 'bold')).pack(side=tk.LEFT)
        
        # Items frame with scrollbar
        items_frame = ttk.Frame(self.main_frame)
        items_frame.pack(fill=tk.BOTH, expand=True)
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(items_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Canvas for scrolling
        self.canvas = tk.Canvas(items_frame, yscrollcommand=scrollbar.set)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        scrollbar.config(command=self.canvas.yview)
        
        # Frame for items in canvas
        self.items_container = ttk.Frame(self.canvas)
        self.canvas.create_window((0, 0), window=self.items_container, anchor=tk.NW, tags="items_container")
        
        # Configure canvas scrolling
        self.items_container.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox(tk.ALL)))
        
        # Mouse wheel scrolling
        self.canvas.bind_all("<MouseWheel>", lambda e: self.canvas.yview_scroll(int(-1*(e.delta/120)), "units"))
        
        # Button frame
        button_frame = ttk.Frame(self.main_frame)
        button_frame.pack(fill=tk.X, pady=(10, 0))
        
        # Buttons
        view_more_button = ttk.Button(button_frame, text="View More...", command=self.view_more)
        view_more_button.pack(side=tk.RIGHT)
        
        # Popup keyboard shortcut
        self.popup.bind("<Escape>", lambda e: self.hide_popup())
        
        # Set up window close event
        self.popup.protocol("WM_DELETE_WINDOW", self.hide_popup)
        
    def show_popup(self, event=None):
        """Show the popup with recent clipboard items"""
        # Get recent items
        items = self.db_manager.get_recent_items(10)  # Get 10 most recent items
        
        # Clear previous items
        for widget in self.items_container.winfo_children():
            widget.destroy()
            
        # If no items, show message
        if not items:
            ttk.Label(self.items_container, text="No clipboard history available").pack(pady=20)
        else:
            # Add items to popup
            for item in items:
                self.add_item_to_popup(item)
                
        # Update canvas
        self.canvas.update_idletasks()
        self.canvas.configure(scrollregion=self.canvas.bbox(tk.ALL))
        
        # Position popup in the center of the screen
        screen_width = self.popup.winfo_screenwidth()
        screen_height = self.popup.winfo_screenheight()
        
        popup_width = 400
        popup_height = 300
        
        x = (screen_width // 2) - (popup_width // 2)
        y = (screen_height // 2) - (popup_height // 2)
        
        self.popup.geometry(f"{popup_width}x{popup_height}+{x}+{y}")
        
        # Show popup
        self.popup.deiconify()
        self.popup.focus_force()
        
    def hide_popup(self, event=None):
        """Hide the popup"""
        self.popup.withdraw()
        
    def add_item_to_popup(self, item):
        """Add an item to the popup"""
        if not item:
            return
            
        # Create frame for this item
        item_frame = ttk.Frame(self.items_container)
        item_frame.pack(fill=tk.X, pady=5)
        
        # Format content for display
        content_preview = "[No content]"
        
        if item.get('content'):
            if item.get('type') == ClipItemType.TEXT.value:
                try:
                    text_content = item['content'].decode('utf-8', errors='replace')
                    content_preview = limit_text_length(text_content, 50)
                except Exception as e:
                    content_preview = f"[Error: {str(e)}]"
            else:
                content_preview = "[IMAGE]"
                
        # Item info
        item_id = item.get('id', 0)
        timestamp = format_timestamp(item.get('timestamp'))
        favorite = "★ " if item.get('favorite', False) else ""
        
        # For images, try to show a thumbnail
        if item.get('type') == ClipItemType.IMAGE.value and item.get('content'):
            try:
                # Left side - info and text
                info_frame = ttk.Frame(item_frame)
                info_frame.pack(side=tk.LEFT, fill=tk.X, expand=True)
                
                ttk.Label(info_frame, text=f"{favorite}{timestamp}").pack(anchor=tk.W)
                ttk.Label(info_frame, text=f"[Image]").pack(anchor=tk.W)
                
                # Right side - thumbnail and buttons
                thumbnail_frame = ttk.Frame(item_frame)
                thumbnail_frame.pack(side=tk.RIGHT, padx=5)
                
                # Create thumbnail
                img = Image.open(BytesIO(item['content']))
                img.thumbnail((50, 50))  # Resize to thumbnail
                photo = ImageTk.PhotoImage(img)
                
                # Store reference to prevent garbage collection
                thumbnail_frame.image = photo
                
                # Display thumbnail
                image_label = ttk.Label(thumbnail_frame, image=photo)
                image_label.pack(pady=2)
                
            except Exception as e:
                # If failed to create thumbnail, show text instead
                ttk.Label(item_frame, text=f"{favorite}{timestamp} - [Image Error: {str(e)}]").pack(side=tk.LEFT, fill=tk.X, expand=True)
        else:
            # Text item - show preview
            ttk.Label(item_frame, text=f"{favorite}{timestamp} - {content_preview}").pack(side=tk.LEFT, fill=tk.X, expand=True)
            
        # Buttons frame
        buttons_frame = ttk.Frame(item_frame)
        buttons_frame.pack(side=tk.RIGHT)
        
        # Copy button
        copy_button = ttk.Button(
            buttons_frame, 
            text="Copy", 
            width=6,
            command=lambda i=item: self.copy_item(i)
        )
        copy_button.pack(side=tk.LEFT, padx=2)
        
        # Delete button
        delete_button = ttk.Button(
            buttons_frame, 
            text="×", 
            width=3,
            command=lambda i=item: self.delete_item(i)
        )
        delete_button.pack(side=tk.LEFT)
        
        # Make the entire item clickable
        item_frame.bind("<Button-1>", lambda e, i=item: self.copy_item(i))
        
        # Highlight on hover
        def on_enter(e):
            item_frame.configure(style="Hover.TFrame")
            
        def on_leave(e):
            item_frame.configure(style="TFrame")
            
        # Create hover style
        style = ttk.Style()
        if "Hover.TFrame" not in style.map("TFrame"):
            style.configure("Hover.TFrame", background="#E0E0E0")
            
        item_frame.bind("<Enter>", on_enter)
        item_frame.bind("<Leave>", on_leave)
            
    def copy_item(self, item):
        """Copy item to clipboard and hide popup"""
        if not item:
            return
            
        # Get content
        content = None
        if item.get('content'):
            if item.get('type') == ClipItemType.TEXT.value:
                try:
                    content = item['content'].decode('utf-8', errors='replace')
                    success = ClipboardAdapter.set_text(content)
                    if success:
                        logger.info(f"Copied text from popup: {limit_text_length(content, 30)}")
                    else:
                        logger.error("Failed to copy text to clipboard from popup")
                except Exception as e:
                    logger.error(f"Error copying text: {e}")
            else:
                # Image
                try:
                    success = ClipboardAdapter.set_image(item['content'])
                    if success:
                        logger.info("Copied image from popup")
                    else:
                        logger.error("Failed to copy image to clipboard from popup")
                except Exception as e:
                    logger.error(f"Error copying image: {e}")
                    
        # Hide popup
        self.hide_popup()
        
    def delete_item(self, item):
        """Delete item and refresh popup"""
        if not item:
            return
            
        # Delete from database
        success = self.db_manager.delete_item(item['id'])
        
        if success:
            logger.info(f"Deleted item {item['id']} from popup")
            # Refresh popup
            self.show_popup()
        else:
            logger.error(f"Failed to delete item {item['id']}")
            
    def view_more(self):
        """Open main application window"""
        # This would typically launch the main application
        # For now we'll just hide the popup
        self.hide_popup()
        logger.info("View more requested - would launch main window")
        
    def start_keyboard_listener(self):
        """Start the keyboard listener thread"""
        if not self.keyboard_listener:
            self.keyboard_listener = KeyboardListener(self.show_popup)
            self.keyboard_listener.start()
            
    def stop_keyboard_listener(self):
        """Stop the keyboard listener thread"""
        if self.keyboard_listener:
            self.keyboard_listener.stop()
            self.keyboard_listener.join(timeout=1.0)
            self.keyboard_listener = None

def main():
    """Standalone quick paste popup"""
    # Create the popup
    root = tk.Tk()
    root.withdraw()  # Hide the main window
    
    popup = QuickPastePopup(root)
    popup.show_popup()  # Show the popup immediately
    
    # Start keyboard listener
    popup.start_keyboard_listener()
    
    try:
        root.mainloop()
    finally:
        popup.stop_keyboard_listener()

if __name__ == "__main__":
    main()