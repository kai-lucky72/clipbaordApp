#!/usr/bin/env python3
"""
Advanced Clipboard Manager - Tkinter GUI Version

This module implements a graphical user interface for the clipboard manager
using Tkinter, which is included in the Python standard library.
"""
import os
import sys
import logging
import threading
import json
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from tkinter.scrolledtext import ScrolledText
from datetime import datetime
import time
from io import BytesIO
from PIL import Image, ImageTk

from database import DatabaseManager
from clipboard_manager import ClipboardManager, ClipItemType
from clipboard_adapter import ClipboardAdapter
from utils import setup_logger, limit_text_length, format_timestamp
from quick_paste_popup import QuickPastePopup
from keyboard_handler import KeyboardHandler
from tag_manager import TagManager, TagEditorDialog
from theme_manager import ThemeManager, Theme

# Configure logging
setup_logger()
logger = logging.getLogger(__name__)

class ClipboardManagerTkGUI:
    """
    Main application class for the Tkinter GUI version of Clipboard Manager
    """
    
    def __init__(self, root):
        """Initialize the application"""
        self.root = root
        self.root.title("Advanced Clipboard Manager")
        self.root.geometry("900x650")
        self.root.minsize(700, 500)
        
        # Set theme
        self.setup_theme()
        
        # Set icon if available
        try:
            # Try different icon formats based on platform
            icon_path = None
            if os.path.exists("assets/icon.ico"):
                icon_path = "assets/icon.ico"
            elif os.path.exists("assets/icon.png"):
                icon_path = "assets/icon.png"
            elif os.path.exists("generated-icon.png"):
                icon_path = "generated-icon.png"
                
            if icon_path and icon_path.endswith('.png'):
                # For platforms that support PhotoImage
                icon = ImageTk.PhotoImage(file=icon_path)
                self.root.tk.call('wm', 'iconphoto', self.root._w, icon)
            elif icon_path:
                self.root.iconbitmap(icon_path)
        except Exception as e:
            logger.debug(f"Icon not found or not supported: {e}")
        
        # Initialize database and clipboard manager
        self.db_manager = DatabaseManager()
        self.clipboard_manager = ClipboardManager(self.db_manager)
        
        # State variables
        self.clipboard_items = []
        self.current_filter = "all"  # "all", "text", "image", "favorites"
        self.search_text = ""
        self.selected_item = None
        self.last_tags = []  # Store recently used tags
        
        # Animation settings
        self.animation_frames = 10  # Number of frames for transitions
        self.animation_duration = 200  # Duration in milliseconds
        self.animation_running = False  # Flag to prevent multiple animations
        self.transition_effects = True  # Toggle for transition effects
        
        # Create main layout
        self.create_menu()
        self.create_main_layout()
        
        # Set up keyboard shortcuts
        self.setup_keyboard_shortcuts()
        
        # Start clipboard monitoring
        self.clipboard_manager.start_monitoring()
        
        # Set up periodic refresh
        self._schedule_refresh()
        
        # Clean up on exit
        self.root.protocol("WM_DELETE_WINDOW", self.on_exit)
        
        logger.info("Tkinter GUI initialized")
        
    def setup_theme(self):
        """Set up a modern theme for the application with micro-interactions"""
        style = ttk.Style()
        
        # Try to use a more modern theme if available
        available_themes = style.theme_names()
        preferred_themes = ['clam', 'alt', 'classic']
        
        for theme in preferred_themes:
            if theme in available_themes:
                style.theme_use(theme)
                break
                
        # Customize specific elements
        style.configure('TButton', padding=6)
        style.configure('TFrame', background='#F0F0F0')
        style.configure('Treeview', rowheight=25)
        style.configure('Treeview.Heading', font=('Arial', 10, 'bold'))
        
        # Configure tags for the treeview with better selection and hover effects
        style.map('Treeview',
                 background=[('selected', '#0078D7')],
                 foreground=[('selected', 'white')])
                 
        # Create custom button styles for micro-interactions
        style.configure('Action.TButton', padding=6, background='#E1E1E1')
        style.map('Action.TButton',
                 background=[('active', '#D1D1D1'), ('pressed', '#C1C1C1')],
                 relief=[('pressed', 'sunken'), ('!pressed', 'raised')])
        
        # Create hover style for list items
        style.configure('Hover.TFrame', background='#E8E8E8')
        
        # Create selected style for list items
        style.configure('Selected.TFrame', background='#CCE4F7')
        
        # Create favorite item style
        style.configure('Favorite.TFrame', background='#FFF8E1')
                 
    def setup_keyboard_shortcuts(self):
        """Set up keyboard shortcuts for common actions"""
        # Copy - Ctrl+C
        self.root.bind('<Control-c>', lambda e: self.copy_selected_item())
        
        # Delete - Delete key
        self.root.bind('<Delete>', lambda e: self.delete_selected_item())
        
        # Toggle favorite - Ctrl+F
        self.root.bind('<Control-f>', lambda e: self.toggle_favorite())
        
        # Refresh - F5
        self.root.bind('<F5>', lambda e: self.refresh_items())
        
        # Search focus - Ctrl+S
        self.root.bind('<Control-s>', lambda e: self.search_entry.focus_set())
        
        # Quick add text - Ctrl+N
        self.root.bind('<Control-n>', lambda e: self.show_add_text_dialog())
        
        # Manage tags - Ctrl+T
        self.root.bind('<Control-t>', lambda e: self.manage_tags())
    
    def create_menu(self):
        """Create the main menu"""
        menu_bar = tk.Menu(self.root)
        
        # File menu
        file_menu = tk.Menu(menu_bar, tearoff=0)
        file_menu.add_command(label="Refresh", command=self.refresh_items)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.on_exit)
        menu_bar.add_cascade(label="File", menu=file_menu)
        
        # Edit menu
        edit_menu = tk.Menu(menu_bar, tearoff=0)
        edit_menu.add_command(label="Copy", command=self.copy_selected_item)
        edit_menu.add_command(label="Delete", command=self.delete_selected_item)
        edit_menu.add_separator()
        edit_menu.add_command(label="Clear History", command=self.clear_history)
        menu_bar.add_cascade(label="Edit", menu=edit_menu)
        
        # Settings menu
        settings_menu = tk.Menu(menu_bar, tearoff=0)
        self.track_images_var = tk.BooleanVar(value=self.clipboard_manager.track_images)
        settings_menu.add_checkbutton(label="Track Images", 
                                     variable=self.track_images_var,
                                     command=self.toggle_track_images)
        
        # Add animation toggle and sub-menu
        self.animation_var = tk.BooleanVar(value=self.transition_effects)
        settings_menu.add_checkbutton(label="Enable Animations", 
                                    variable=self.animation_var,
                                    command=self.toggle_animations)
                                    
        # Animation settings submenu
        anim_menu = tk.Menu(settings_menu, tearoff=0)
        
        # Animation speed options
        anim_menu.add_command(label="Fast Animations", 
                             command=lambda: self.set_animation_speed("fast"))
        anim_menu.add_command(label="Normal Animations", 
                             command=lambda: self.set_animation_speed("normal"))
        anim_menu.add_command(label="Slow Animations", 
                             command=lambda: self.set_animation_speed("slow"))
                             
        settings_menu.add_cascade(label="Animation Settings", menu=anim_menu)
        
        menu_bar.add_cascade(label="Settings", menu=settings_menu)
        
        # Help menu
        help_menu = tk.Menu(menu_bar, tearoff=0)
        help_menu.add_command(label="About", command=self.show_about)
        menu_bar.add_cascade(label="Help", menu=help_menu)
        
        self.root.config(menu=menu_bar)
    
    def create_main_layout(self):
        """Create the main application layout"""
        # Main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Top controls frame
        controls_frame = ttk.Frame(main_frame)
        controls_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Search entry
        ttk.Label(controls_frame, text="Search:").pack(side=tk.LEFT, padx=(0, 5))
        self.search_entry = ttk.Entry(controls_frame, width=30)
        self.search_entry.pack(side=tk.LEFT, padx=(0, 10))
        self.search_entry.bind("<KeyRelease>", self.on_search_changed)
        
        # Filter combobox
        ttk.Label(controls_frame, text="Filter:").pack(side=tk.LEFT, padx=(0, 5))
        self.filter_combo = ttk.Combobox(controls_frame, 
                                        values=["All Items", "Text Only", "Images Only", "Favorites"],
                                        width=15,
                                        state="readonly")
        self.filter_combo.current(0)
        self.filter_combo.pack(side=tk.LEFT)
        self.filter_combo.bind("<<ComboboxSelected>>", self.on_filter_changed)
        
        # Refresh button
        refresh_button = ttk.Button(controls_frame, text="Refresh", command=self.refresh_items)
        refresh_button.pack(side=tk.RIGHT)
        
        # Create paned window for list and preview
        paned_window = ttk.PanedWindow(main_frame, orient=tk.HORIZONTAL)
        paned_window.pack(fill=tk.BOTH, expand=True)
        
        # Left frame - clipboard items list
        left_frame = ttk.Frame(paned_window)
        paned_window.add(left_frame, weight=1)
        
        # Create treeview for clipboard items
        columns = ("id", "type", "timestamp", "preview", "favorite")
        self.tree = ttk.Treeview(left_frame, columns=columns, show="headings", selectmode="browse")
        
        # Configure columns
        self.tree.heading("id", text="ID")
        self.tree.heading("type", text="Type")
        self.tree.heading("timestamp", text="Time")
        self.tree.heading("preview", text="Content")
        self.tree.heading("favorite", text="★")
        
        # Set column widths
        self.tree.column("id", width=50, stretch=False)
        self.tree.column("type", width=70, stretch=False)
        self.tree.column("timestamp", width=120, stretch=False)
        self.tree.column("preview", width=300)
        self.tree.column("favorite", width=30, stretch=False)
        
        # Add scrollbar
        scrollbar = ttk.Scrollbar(left_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        # Pack tree and scrollbar
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Bind selection event
        self.tree.bind("<<TreeviewSelect>>", self.on_item_selected)
        self.tree.bind("<Double-1>", self.on_item_double_clicked)
        self.tree.bind("<Button-3>", self.show_context_menu)  # Right-click
        
        # Right frame - preview
        right_frame = ttk.Frame(paned_window)
        paned_window.add(right_frame, weight=1)
        
        # Preview frame title
        preview_label = ttk.Label(right_frame, text="Preview")
        preview_label.pack(anchor=tk.W, pady=(0, 5))
        
        # Preview content
        self.preview_frame = ttk.Frame(right_frame, relief=tk.SUNKEN, borderwidth=1)
        self.preview_frame.pack(fill=tk.BOTH, expand=True)
        
        # Default preview - text
        self.preview_text = ScrolledText(self.preview_frame, wrap=tk.WORD, width=40, height=20)
        self.preview_text.pack(fill=tk.BOTH, expand=True)
        
        # Button frame at bottom
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(10, 0))
        
        # Action buttons
        copy_button = ttk.Button(button_frame, text="Copy", command=self.copy_selected_item)
        copy_button.pack(side=tk.LEFT, padx=(0, 5))
        
        delete_button = ttk.Button(button_frame, text="Delete", command=self.delete_selected_item)
        delete_button.pack(side=tk.LEFT, padx=(0, 5))
        
        favorite_button = ttk.Button(button_frame, text="Toggle Favorite", command=self.toggle_favorite)
        favorite_button.pack(side=tk.LEFT)
        
        # Status bar
        self.status_var = tk.StringVar()
        self.status_var.set("Ready")
        status_bar = ttk.Label(main_frame, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.pack(fill=tk.X, pady=(10, 0))
        
        # Initial load
        self.refresh_items()
    
    def refresh_items(self):
        """Refresh the clipboard items list"""
        # Clear existing items
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # Get items based on current filter and search
        filter_type = None
        favorites_only = False
        
        if self.current_filter == "text":
            filter_type = ClipItemType.TEXT.value
        elif self.current_filter == "image":
            filter_type = ClipItemType.IMAGE.value
        elif self.current_filter == "favorites":
            favorites_only = True
            
        self.clipboard_items = self.db_manager.get_all_items(
            search_text=self.search_text, 
            filter_type=filter_type,
            favorites_only=favorites_only
        )
        
        # Add items to treeview
        for item in self.clipboard_items:
            item_id = item.get('id', 0)
            item_type = item.get('type', '')
            timestamp = format_timestamp(item.get('timestamp', datetime.now()))
            favorite = "★" if item.get('favorite', False) else ""
            
            # Generate preview
            preview = "[No content]"
            if item.get('content'):
                if item_type == ClipItemType.TEXT.value:
                    try:
                        text_content = item['content'].decode('utf-8', errors='replace')
                        preview = limit_text_length(text_content, 50)
                    except Exception as e:
                        preview = f"[Error: {str(e)}]"
                else:
                    preview = "[IMAGE]"
            
            # Insert into tree
            item_iid = self.tree.insert("", tk.END, values=(item_id, item_type, timestamp, preview, favorite))
            
            # Apply tags for favorites to highlight them
            if item.get('favorite', False):
                self.tree.item(item_iid, tags=('favorite',))
        
        # Add hover binding to each item for micro-interactions
        # Note: The tkinter event binding can be platform-dependent
        # We'll only add if the platform supports these events
        try:
            for item_iid in self.tree.get_children():
                # Add hover effect with <Enter> and <Leave> events
                self.tree.tag_bind(item_iid, '<Enter>', lambda e, iid=item_iid: self.on_item_hover_enter(e, iid))
                self.tree.tag_bind(item_iid, '<Leave>', lambda e, iid=item_iid: self.on_item_hover_leave(e, iid))
        except Exception as e:
            logger.debug(f"Could not add hover effects: {e}")

        # Configure tag appearance for favorites
        self.tree.tag_configure('favorite', background='#FFF8E1')
        # Configure hover tag
        self.tree.tag_configure('hover', background='#E8E8E8')
        # Configure selected tag with animation-like feel
        self.tree.tag_configure('selected', background='#CCE4F7')
        
        self.status_var.set(f"Loaded {len(self.clipboard_items)} items")
        
        # Clear preview if no items
        if not self.clipboard_items:
            self.clear_preview()
            
    def on_item_hover_enter(self, event, item_iid):
        """Handle mouse hover enter for tree items"""
        # Skip if this item is already selected
        if item_iid in self.tree.selection():
            return
            
        # Add hover tag
        current_tags = list(self.tree.item(item_iid, 'tags'))
        if 'hover' not in current_tags:
            current_tags.append('hover')
            self.tree.item(item_iid, tags=current_tags)
    
    def on_item_hover_leave(self, event, item_iid):
        """Handle mouse hover leave for tree items"""
        # Remove hover tag if present
        current_tags = list(self.tree.item(item_iid, 'tags'))
        if 'hover' in current_tags:
            current_tags.remove('hover')
            self.tree.item(item_iid, tags=current_tags)
    
    def on_search_changed(self, event):
        """Handle search text changes"""
        self.search_text = self.search_entry.get()
        self.refresh_items()
    
    def on_filter_changed(self, event):
        """Handle filter changes"""
        filter_text = self.filter_combo.get()
        
        if filter_text == "All Items":
            self.current_filter = "all"
        elif filter_text == "Text Only":
            self.current_filter = "text"
        elif filter_text == "Images Only":
            self.current_filter = "image"
        elif filter_text == "Favorites":
            self.current_filter = "favorites"
            
        self.refresh_items()
    
    def on_item_selected(self, event):
        """Handle selection in the treeview"""
        selected_items = self.tree.selection()
        if not selected_items:
            return
            
        item_id_str = self.tree.item(selected_items[0], "values")[0]
        
        try:
            item_id = int(item_id_str)
            self.selected_item = next((item for item in self.clipboard_items if item.get('id') == item_id), None)
            
            if self.selected_item:
                self.update_preview(self.selected_item)
            else:
                self.clear_preview()
        except (ValueError, IndexError):
            self.clear_preview()
    
    def update_preview(self, item):
        """Update the preview with the selected item using animated transitions"""
        # Skip animation if it's disabled or already running
        if not self.transition_effects or self.animation_running:
            # Just perform the regular update
            self._update_preview_content(item)
            return
            
        # Start animation
        self.animation_running = True
        
        # Create a temporary frame for the animation
        temp_frame = ttk.Frame(self.root)
        
        # Take a "screenshot" of the current preview
        old_width = self.preview_frame.winfo_width()
        old_height = self.preview_frame.winfo_height()
        
        # Animate the transition - fade out current content
        self._animate_fade_out(self.preview_frame, 
                              callback=lambda: self._update_preview_with_animation(item))
    
    def _animate_fade_out(self, widget, callback=None):
        """Animate a widget fading out"""
        frames = self.animation_frames
        duration_per_frame = self.animation_duration / frames
        
        # Start at full opacity
        alpha = 1.0
        
        def fade_step():
            nonlocal alpha
            alpha -= 1.0 / frames
            
            if alpha <= 0:
                # Animation complete, call the callback if provided
                if callback:
                    callback()
                return
                
            # Apply "fading" effect by changing background color
            # In Tkinter, we can simulate transparency by adjusting the background color
            r, g, b = 240, 240, 240  # Base color #F0F0F0
            fade_color = f'#{int(r * alpha):02x}{int(g * alpha):02x}{int(b * alpha):02x}'
            
            try:
                for child in widget.winfo_children():
                    if isinstance(child, ttk.Frame):
                        child.configure(style='Fade.TFrame')
                
                # Schedule next frame
                self.root.after(int(duration_per_frame), fade_step)
            except tk.TclError:
                # Widget might have been destroyed
                pass
        
        # Create fade style
        style = ttk.Style()
        style.configure('Fade.TFrame', background='#F0F0F0')
        
        # Start animation
        fade_step()
    
    def _animate_fade_in(self, widget, callback=None):
        """Animate a widget fading in"""
        frames = self.animation_frames
        duration_per_frame = self.animation_duration / frames
        
        # Start at zero opacity
        alpha = 0.0
        
        def fade_step():
            nonlocal alpha
            alpha += 1.0 / frames
            
            if alpha >= 1.0:
                # Animation complete, call the callback if provided
                if callback:
                    callback()
                self.animation_running = False
                return
                
            # Apply "fading" effect by changing background color
            r, g, b = 240, 240, 240  # Base color #F0F0F0
            fade_color = f'#{int(r * alpha):02x}{int(g * alpha):02x}{int(b * alpha):02x}'
            
            try:
                for child in widget.winfo_children():
                    if isinstance(child, ttk.Frame):
                        child.configure(style='Fade.TFrame')
                
                # Schedule next frame
                self.root.after(int(duration_per_frame), fade_step)
            except tk.TclError:
                # Widget might have been destroyed
                pass
        
        # Create fade style
        style = ttk.Style()
        style.configure('Fade.TFrame', background='#F0F0F0')
        
        # Start animation
        fade_step()
        
    def _update_preview_with_animation(self, item):
        """Update preview content and then animate it fading in"""
        # Update the content
        self._update_preview_content(item)
        
        # Animate the new content fading in
        self._animate_fade_in(self.preview_frame)
        
    def _update_preview_content(self, item):
        """Update the preview content without animation"""
        # Clear previous preview
        for widget in self.preview_frame.winfo_children():
            widget.destroy()
            
        if not item or not item.get('content'):
            # Show empty preview
            self.preview_text = ScrolledText(self.preview_frame, wrap=tk.WORD)
            self.preview_text.insert(tk.END, "No content to display")
            self.preview_text.configure(state=tk.DISABLED)
            self.preview_text.pack(fill=tk.BOTH, expand=True)
            return
            
        item_type = item.get('type')
        
        if item_type == ClipItemType.TEXT.value:
            # Text preview
            try:
                text_content = item['content'].decode('utf-8', errors='replace')
                self.preview_text = ScrolledText(self.preview_frame, wrap=tk.WORD)
                self.preview_text.insert(tk.END, text_content)
                self.preview_text.pack(fill=tk.BOTH, expand=True)
            except Exception as e:
                self.preview_text = ScrolledText(self.preview_frame, wrap=tk.WORD)
                self.preview_text.insert(tk.END, f"Error displaying content: {str(e)}")
                self.preview_text.configure(state=tk.DISABLED)
                self.preview_text.pack(fill=tk.BOTH, expand=True)
                
        elif item_type == ClipItemType.IMAGE.value:
            # Image preview
            try:
                frame = ttk.Frame(self.preview_frame)
                frame.pack(fill=tk.BOTH, expand=True)
                
                # Try to display the image
                img = Image.open(BytesIO(item['content']))
                
                # Resize if needed to fit the preview area
                width, height = img.size
                max_width = 400
                max_height = 400
                
                if width > max_width or height > max_height:
                    # Calculate scaling factor
                    scale = min(max_width / width, max_height / height)
                    new_width = int(width * scale)
                    new_height = int(height * scale)
                    img = img.resize((new_width, new_height), Image.LANCZOS)
                
                photo = ImageTk.PhotoImage(img)
                
                # Keep a reference to prevent garbage collection
                self.current_image = photo
                
                # Display in a label
                image_label = ttk.Label(frame, image=photo)
                image_label.pack(pady=10)
                
                # Add image info
                info_text = f"Format: {img.format}\nSize: {width}x{height} pixels"
                info_label = ttk.Label(frame, text=info_text)
                info_label.pack(pady=5)
                
                # Add save button
                save_button = ttk.Button(frame, text="Save Image", 
                                        command=lambda: self.save_image(item))
                save_button.pack(pady=10)
                
            except Exception as e:
                # Show error
                self.preview_text = ScrolledText(self.preview_frame, wrap=tk.WORD)
                self.preview_text.insert(tk.END, f"Error displaying image: {str(e)}")
                self.preview_text.configure(state=tk.DISABLED)
                self.preview_text.pack(fill=tk.BOTH, expand=True)
        
        else:
            # Unknown type
            self.preview_text = ScrolledText(self.preview_frame, wrap=tk.WORD)
            self.preview_text.insert(tk.END, f"Unsupported content type: {item_type}")
            self.preview_text.configure(state=tk.DISABLED)
            self.preview_text.pack(fill=tk.BOTH, expand=True)
    
    def clear_preview(self):
        """Clear the preview area"""
        for widget in self.preview_frame.winfo_children():
            widget.destroy()
            
        self.preview_text = ScrolledText(self.preview_frame, wrap=tk.WORD)
        self.preview_text.insert(tk.END, "No item selected")
        self.preview_text.configure(state=tk.DISABLED)
        self.preview_text.pack(fill=tk.BOTH, expand=True)
    
    def on_item_double_clicked(self, event):
        """Handle double-click on an item"""
        self.copy_selected_item()
    
    def copy_selected_item(self):
        """Copy the selected item to clipboard"""
        if not self.selected_item:
            messagebox.showinfo("Info", "No item selected")
            return
            
        content = self.clipboard_manager.get_clipboard_content(self.selected_item)
        
        if content is None:
            messagebox.showerror("Error", "Failed to copy item to clipboard")
            return
            
        success = False
        if self.selected_item['type'] == ClipItemType.TEXT.value:
            success = ClipboardAdapter.set_text(content)
            if success:
                self.status_var.set(f"Copied text to clipboard: {limit_text_length(content, 30)}")
            else:
                messagebox.showerror("Error", "Failed to copy text to clipboard")
        else:
            success = ClipboardAdapter.set_image(content)
            if success:
                self.status_var.set("Copied image to clipboard")
            else:
                messagebox.showerror("Error", "Failed to copy image to clipboard")
    
    def delete_selected_item(self):
        """Delete the selected item"""
        if not self.selected_item:
            messagebox.showinfo("Info", "No item selected")
            return
            
        if messagebox.askyesno("Confirm Delete", "Are you sure you want to delete this item?"):
            result = self.db_manager.delete_item(self.selected_item['id'])
            
            if result:
                self.status_var.set(f"Item {self.selected_item['id']} deleted")
                self.refresh_items()
            else:
                messagebox.showerror("Error", "Failed to delete item")
    
    def toggle_favorite(self):
        """Toggle favorite status for the selected item"""
        if not self.selected_item:
            messagebox.showinfo("Info", "No item selected")
            return
            
        result = self.db_manager.toggle_favorite(self.selected_item['id'])
        
        if result is not None:
            state = "added to" if result else "removed from"
            self.status_var.set(f"Item {self.selected_item['id']} {state} favorites")
            self.refresh_items()
        else:
            messagebox.showerror("Error", "Failed to update favorite status")
    
    def clear_history(self):
        """Clear clipboard history"""
        if messagebox.askyesno("Confirm Clear", "Clear clipboard history?\nFavorites will be kept."):
            count = self.db_manager.clear_history(keep_favorites=True)
            self.status_var.set(f"Cleared {count} non-favorite items from history")
            self.refresh_items()
    
    def toggle_track_images(self):
        """Toggle image tracking"""
        track_images = self.track_images_var.get()
        self.clipboard_manager.set_track_images(track_images)
        self.status_var.set(f"Image tracking {'enabled' if track_images else 'disabled'}")
        
    def toggle_animations(self):
        """Toggle animation effects"""
        self.transition_effects = self.animation_var.get()
        status = "enabled" if self.transition_effects else "disabled"
        self.status_var.set(f"Animations {status}")
        
    def set_animation_speed(self, speed):
        """Set animation speed"""
        if speed == "fast":
            self.animation_frames = 5
            self.animation_duration = 100
        elif speed == "normal":
            self.animation_frames = 10
            self.animation_duration = 200
        elif speed == "slow":
            self.animation_frames = 15
            self.animation_duration = 400
            
        self.status_var.set(f"Animation speed set to {speed}")
    
    def show_context_menu(self, event):
        """Show context menu for right-click on item"""
        selection = self.tree.selection()
        if not selection:
            return
            
        # Create context menu
        context_menu = tk.Menu(self.root, tearoff=0)
        context_menu.add_command(label="Copy", command=self.copy_selected_item)
        context_menu.add_command(label="Delete", command=self.delete_selected_item)
        context_menu.add_command(label="Toggle Favorite", command=self.toggle_favorite)
        
        # Add tagging options
        context_menu.add_separator()
        context_menu.add_command(label="Add Tag...", command=self.add_tag_to_selected)
        
        # If item has tags, show manage tags option
        if self.selected_item and self.selected_item.get('tags'):
            context_menu.add_command(label="Manage Tags", command=lambda: self.manage_tags(self.selected_item))
        
        # If it's an image, add save option
        if self.selected_item and self.selected_item.get('type') == ClipItemType.IMAGE.value:
            context_menu.add_separator()
            context_menu.add_command(label="Save Image", 
                                     command=lambda: self.save_image(self.selected_item))
        
        # Display context menu
        try:
            context_menu.tk_popup(event.x_root, event.y_root)
        finally:
            context_menu.grab_release()
    
    def save_image(self, item):
        """Save image to file"""
        if not item or not item.get('content') or item.get('type') != ClipItemType.IMAGE.value:
            messagebox.showerror("Error", "No valid image to save")
            return
            
        try:
            # Try to determine format
            img = Image.open(BytesIO(item['content']))
            file_format = img.format.lower() if img.format else "png"
            
            # Open save dialog
            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
            filename = f"clipboard_image_{timestamp}.{file_format}"
            
            file_path = filedialog.asksaveasfilename(
                defaultextension=f".{file_format}",
                filetypes=[
                    (f"{file_format.upper()} files", f"*.{file_format}"),
                    ("All files", "*.*")
                ],
                initialfile=filename
            )
            
            if not file_path:
                return  # User cancelled
                
            # Save the file
            with open(file_path, 'wb') as f:
                f.write(item['content'])
                
            self.status_var.set(f"Image saved to {os.path.basename(file_path)}")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save image: {str(e)}")
    
    def show_about(self):
        """Show about dialog"""
        messagebox.showinfo(
            "About Advanced Clipboard Manager",
            "Advanced Clipboard Manager\n"
            "Version 1.0\n\n"
            "A powerful clipboard manager for keeping track of\n"
            "copied text and images.\n\n"
            "© 2025 Clipboard Manager Project"
        )
    
    def _schedule_refresh(self):
        """Schedule periodic refresh of the clipboard items"""
        self.refresh_items()
        # Schedule next refresh after 10 seconds
        self.root.after(10000, self._schedule_refresh)
    
    def on_exit(self):
        """Clean up resources and exit"""
        try:
            # Stop clipboard monitoring
            if self.clipboard_manager:
                self.clipboard_manager.stop_monitoring()
                
            # Exit application
            self.root.destroy()
            
        except Exception as e:
            logger.error(f"Error during application exit: {e}")

    def show_add_text_dialog(self, event=None):
        """Show dialog to add text directly"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Add Text to Clipboard")
        dialog.geometry("500x350")
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Make dialog modal
        dialog.focus_set()
        
        # Text input
        ttk.Label(dialog, text="Enter text to add:").pack(anchor=tk.W, padx=10, pady=(10, 5))
        
        # Text area with scrollbars
        frame = ttk.Frame(dialog)
        frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))
        
        # Scrollbars
        y_scrollbar = ttk.Scrollbar(frame)
        y_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        text_area = tk.Text(frame, wrap=tk.WORD, yscrollcommand=y_scrollbar.set)
        text_area.pack(fill=tk.BOTH, expand=True)
        
        y_scrollbar.config(command=text_area.yview)
        
        # Tags frame
        tags_frame = ttk.Frame(dialog)
        tags_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        ttk.Label(tags_frame, text="Tags (comma separated):").pack(side=tk.LEFT)
        
        tags_entry = ttk.Entry(tags_frame)
        tags_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(5, 0))
        
        # Button frame
        button_frame = ttk.Frame(dialog)
        button_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        def add_text():
            text = text_area.get("1.0", tk.END).strip()
            if not text:
                messagebox.showwarning("Warning", "Please enter some text")
                return
                
            # Add to clipboard
            item_id = self.db_manager.add_clipboard_item(text.encode('utf-8'), ClipItemType.TEXT.value)
            
            # Add tags if provided
            tags_text = tags_entry.get().strip()
            if tags_text:
                tags = [tag.strip() for tag in tags_text.split(',') if tag.strip()]
                for tag in tags:
                    self.db_manager.add_tag(item_id, tag)
                    
                    # Update last used tags
                    if tag not in self.last_tags:
                        self.last_tags.append(tag)
                        if len(self.last_tags) > 10:  # Keep only last 10 tags
                            self.last_tags.pop(0)
            
            if ClipboardAdapter.set_text(text):
                self.status_var.set(f"Added text to clipboard")
            else:
                self.status_var.set(f"Added text to history but failed to set clipboard")
                
            self.refresh_items()
            dialog.destroy()
        
        cancel_button = ttk.Button(button_frame, text="Cancel", command=dialog.destroy)
        cancel_button.pack(side=tk.RIGHT, padx=(5, 0))
        
        add_button = ttk.Button(button_frame, text="Add", command=add_text)
        add_button.pack(side=tk.RIGHT)
        
        # Set initial focus
        text_area.focus_set()
        
        # Center dialog
        dialog.update_idletasks()
        width = dialog.winfo_width()
        height = dialog.winfo_height()
        x = (self.root.winfo_width() // 2) - (width // 2) + self.root.winfo_x()
        y = (self.root.winfo_height() // 2) - (height // 2) + self.root.winfo_y()
        dialog.geometry(f"{width}x{height}+{x}+{y}")
        
    def add_tag_to_selected(self, event=None):
        """Add a tag to the selected item"""
        if not self.selected_item:
            messagebox.showinfo("Info", "No item selected")
            return
            
        dialog = tk.Toplevel(self.root)
        dialog.title("Add Tag")
        dialog.geometry("300x150")
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Make dialog modal
        dialog.focus_set()
        
        # Tag input
        ttk.Label(dialog, text="Enter tag:", font=("Helvetica", 10, "bold")).pack(anchor=tk.W, padx=10, pady=(10, 5))
        
        tag_var = tk.StringVar()
        tag_combo = ttk.Combobox(dialog, textvariable=tag_var)
        tag_combo.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        # Add recent tags to dropdown
        if self.last_tags:
            tag_combo['values'] = self.last_tags
        
        # Category checkbox
        category_var = tk.BooleanVar(value=False)
        category_check = ttk.Checkbutton(dialog, text="Create as category tag (add # prefix)", variable=category_var)
        category_check.pack(anchor=tk.W, padx=10, pady=(0, 10))
        
        # Buttons
        button_frame = ttk.Frame(dialog)
        button_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        def add_tag():
            tag = tag_var.get().strip()
            if not tag:
                messagebox.showwarning("Warning", "Please enter a tag")
                return
                
            # Add category prefix if needed
            if category_var.get() and not (tag.startswith("#") or tag.startswith("@")):
                tag = "#" + tag
                
            # Check if tag already exists for this item
            if self.selected_item and 'tags' in self.selected_item and self.selected_item['tags']:
                try:
                    # Parse JSON tags array
                    tags_list = json.loads(self.selected_item['tags'])
                    if tag in tags_list:
                        messagebox.showinfo("Info", f"Tag '{tag}' already exists for this item")
                        return
                except Exception as e:
                    logger.error(f"Error parsing tags: {e}")
                
            # Add tag to item
            result = self.db_manager.add_tag(self.selected_item['id'], tag)
            
            if result:
                # Update last used tags
                if tag not in self.last_tags:
                    self.last_tags.append(tag)
                    if len(self.last_tags) > 10:  # Keep only last 10 tags
                        self.last_tags.pop(0)
                        
                self.status_var.set(f"Added tag '{tag}' to item {self.selected_item['id']}")
                self.refresh_items()
            else:
                messagebox.showerror("Error", f"Failed to add tag '{tag}'")
                
            dialog.destroy()
        
        cancel_button = ttk.Button(button_frame, text="Cancel", command=dialog.destroy)
        cancel_button.pack(side=tk.RIGHT, padx=(5, 0))
        
        add_button = ttk.Button(button_frame, text="Add", command=add_tag)
        add_button.pack(side=tk.RIGHT)
        
        # Set initial focus
        tag_combo.focus_set()
        
        # Center dialog
        dialog.update_idletasks()
        width = dialog.winfo_width()
        height = dialog.winfo_height()
        x = (self.root.winfo_width() // 2) - (width // 2) + self.root.winfo_x()
        y = (self.root.winfo_height() // 2) - (height // 2) + self.root.winfo_y()
        dialog.geometry(f"{width}x{height}+{x}+{y}")
        
    def manage_tags(self, item=None):
        """Manage tags for an item using the enhanced TagEditorDialog"""
        if not item:
            item = self.selected_item
            
        if not item:
            messagebox.showinfo("Info", "No item selected")
            return
            
        # Use the enhanced tag editor dialog
        from tag_manager import TagEditorDialog, TagManager
        tag_manager = TagManager(self.db_manager)
        TagEditorDialog(self.root, item['id'], tag_manager)
        
        # Refresh the display to show updated tags
        self.refresh_items()


def main():
    """Application entry point"""
    try:
        # Check if we're in a headless environment
        try:
            # Create the main window
            root = tk.Tk()
            
            # Try to get the screen size - this will fail in truly headless environments
            screen_width = root.winfo_screenwidth()
            screen_height = root.winfo_screenheight()
            
            logger.info(f"Display detected: {screen_width}x{screen_height}")
            
            # Create and run the application
            app = ClipboardManagerTkGUI(root)
            
            # Start the main loop
            root.mainloop()
            
        except tk.TclError as e:
            if "couldn't connect to display" in str(e) or "no display" in str(e).lower():
                logger.error("No display available - cannot run GUI")
                print("Error: No display available to run the GUI.")
                print("Please run in CLI mode with: python clipboard_app.py --cli")
                return 1
            else:
                raise
            
    except Exception as e:
        logger.error(f"Error in GUI application: {e}")
        try:
            messagebox.showerror("Error", f"Application error: {str(e)}")
        except:
            print(f"Error in application: {str(e)}")
        return 1
        
    return 0


if __name__ == "__main__":
    sys.exit(main())