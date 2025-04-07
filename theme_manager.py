#!/usr/bin/env python3
"""
Theme Manager Module

This module provides modern theming for the Tkinter GUI.
"""
import tkinter as tk
from tkinter import ttk
import logging
import os
import sys
from enum import Enum

# Configure logging
logger = logging.getLogger(__name__)

class Theme(Enum):
    """Available themes"""
    LIGHT = "light"
    DARK = "dark"
    SYSTEM = "system"

class ThemeManager:
    """
    Manages application theme and styling
    """
    
    def __init__(self, root, theme=Theme.LIGHT):
        """
        Initialize the theme manager
        
        Args:
            root: The root Tkinter window
            theme: The initial theme to apply
        """
        self.root = root
        self.theme = theme
        
        # Apply selected theme
        self.apply_theme(theme)
    
    def apply_theme(self, theme):
        """
        Apply the specified theme
        
        Args:
            theme: The theme to apply
        """
        if theme == Theme.SYSTEM:
            # Try to detect system theme
            theme = self._detect_system_theme()
        
        self.theme = theme
        
        # Create style
        style = ttk.Style()
        
        # Apply theme
        if theme == Theme.DARK:
            self._apply_dark_theme(style)
        else:
            self._apply_light_theme(style)
    
    def _detect_system_theme(self):
        """
        Attempt to detect the system theme
        
        Returns:
            Detected theme or default light theme
        """
        platform = sys.platform
        
        try:
            if platform == 'win32':
                # Windows
                import winreg
                key = winreg.OpenKey(
                    winreg.HKEY_CURRENT_USER,
                    r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize"
                )
                value, _ = winreg.QueryValueEx(key, "AppsUseLightTheme")
                return Theme.LIGHT if value == 1 else Theme.DARK
                
            elif platform == 'darwin':
                # macOS
                import subprocess
                result = subprocess.run(
                    ['defaults', 'read', '-g', 'AppleInterfaceStyle'],
                    capture_output=True,
                    text=True
                )
                return Theme.DARK if result.stdout.strip() == 'Dark' else Theme.LIGHT
                
            elif platform.startswith('linux'):
                # Linux with gsettings (GNOME)
                import subprocess
                try:
                    result = subprocess.run(
                        ['gsettings', 'get', 'org.gnome.desktop.interface', 'gtk-theme'],
                        capture_output=True,
                        text=True
                    )
                    return Theme.DARK if 'dark' in result.stdout.lower() else Theme.LIGHT
                except:
                    pass
        except Exception as e:
            logger.error(f"Error detecting system theme: {e}")
        
        # Default to light theme
        return Theme.LIGHT
    
    def _apply_light_theme(self, style):
        """
        Apply light theme
        
        Args:
            style: ttk.Style instance
        """
        # Set theme colors
        background = "#ffffff"
        foreground = "#333333"
        accent = "#3f51b5"
        accent_light = "#757de8"
        hover = "#e0e0e0"
        button_bg = "#f0f0f0"
        frame_bg = "#f5f5f5"
        
        # Configure style
        style.configure("TFrame", background=background)
        style.configure("TLabel", background=background, foreground=foreground)
        style.configure("TButton", background=button_bg, foreground=foreground)
        style.map("TButton",
            background=[("active", hover), ("pressed", accent_light)],
            foreground=[("active", foreground), ("pressed", foreground)]
        )
        
        style.configure("TEntry", fieldbackground=background, foreground=foreground)
        style.configure("TCombobox", background=button_bg, fieldbackground=background, foreground=foreground)
        style.map("TCombobox",
            fieldbackground=[("readonly", background)],
            selectbackground=[("readonly", accent)]
        )
        
        style.configure("Treeview", background=background, foreground=foreground, fieldbackground=background)
        style.map("Treeview",
            background=[("selected", accent)],
            foreground=[("selected", "white")]
        )
        
        style.configure("Horizontal.TProgressbar", background=accent)
        style.configure("Vertical.TProgressbar", background=accent)
        
        # Create custom styles
        style.configure("Card.TFrame", background=frame_bg, relief="raised", borderwidth=1)
        style.configure("Header.TLabel", font=("Helvetica", 12, "bold"))
        style.configure("Title.TLabel", font=("Helvetica", 14, "bold"))
        style.configure("Subheader.TLabel", font=("Helvetica", 10, "italic"))
        
        style.configure("Primary.TButton", background=accent, foreground="white")
        style.map("Primary.TButton",
            background=[("active", accent_light), ("pressed", accent_light)],
            foreground=[("active", "white"), ("pressed", "white")]
        )
        
        # Configure root window
        self.root.configure(background=background)
        
    def _apply_dark_theme(self, style):
        """
        Apply dark theme
        
        Args:
            style: ttk.Style instance
        """
        # Set theme colors
        background = "#333333"
        foreground = "#f0f0f0"
        accent = "#5c6bc0"
        accent_light = "#8e99f3"
        hover = "#555555"
        button_bg = "#444444"
        frame_bg = "#3a3a3a"
        
        # Configure style
        style.configure("TFrame", background=background)
        style.configure("TLabel", background=background, foreground=foreground)
        style.configure("TButton", background=button_bg, foreground=foreground)
        style.map("TButton",
            background=[("active", hover), ("pressed", accent_light)],
            foreground=[("active", foreground), ("pressed", foreground)]
        )
        
        style.configure("TEntry", fieldbackground="#4a4a4a", foreground=foreground)
        style.configure("TCombobox", background=button_bg, fieldbackground="#4a4a4a", foreground=foreground)
        style.map("TCombobox",
            fieldbackground=[("readonly", "#4a4a4a")],
            selectbackground=[("readonly", accent)]
        )
        
        style.configure("Treeview", background="#4a4a4a", foreground=foreground, fieldbackground="#4a4a4a")
        style.map("Treeview",
            background=[("selected", accent)],
            foreground=[("selected", "white")]
        )
        
        style.configure("Horizontal.TProgressbar", background=accent)
        style.configure("Vertical.TProgressbar", background=accent)
        
        # Create custom styles
        style.configure("Card.TFrame", background=frame_bg, relief="raised", borderwidth=1)
        style.configure("Header.TLabel", font=("Helvetica", 12, "bold"))
        style.configure("Title.TLabel", font=("Helvetica", 14, "bold"))
        style.configure("Subheader.TLabel", font=("Helvetica", 10, "italic"))
        
        style.configure("Primary.TButton", background=accent, foreground="white")
        style.map("Primary.TButton",
            background=[("active", accent_light), ("pressed", accent_light)],
            foreground=[("active", "white"), ("pressed", "white")]
        )
        
        # Configure root window
        self.root.configure(background=background)
    
    def toggle_theme(self):
        """
        Toggle between light and dark theme
        """
        if self.theme == Theme.LIGHT:
            self.apply_theme(Theme.DARK)
        else:
            self.apply_theme(Theme.LIGHT)


def main():
    """Test function"""
    root = tk.Tk()
    root.title("Theme Manager Test")
    root.geometry("800x600")
    
    theme_manager = ThemeManager(root)
    
    # Create a sample UI to test themes
    main_frame = ttk.Frame(root, padding="20")
    main_frame.pack(fill=tk.BOTH, expand=True)
    
    # Header
    header_label = ttk.Label(main_frame, text="Theme Manager Test", style="Title.TLabel")
    header_label.pack(pady=(0, 20))
    
    # Card frame
    card_frame = ttk.Frame(main_frame, style="Card.TFrame", padding="20")
    card_frame.pack(fill=tk.BOTH, padx=20, pady=20)
    
    # Form elements
    ttk.Label(card_frame, text="Enter your name:").pack(anchor=tk.W, pady=(0, 5))
    ttk.Entry(card_frame).pack(fill=tk.X, pady=(0, 10))
    
    ttk.Label(card_frame, text="Select your country:").pack(anchor=tk.W, pady=(0, 5))
    ttk.Combobox(card_frame, values=["USA", "Canada", "UK", "Australia"]).pack(fill=tk.X, pady=(0, 10))
    
    ttk.Button(card_frame, text="Submit").pack(anchor=tk.W, pady=(10, 0))
    
    # Theme toggle button
    theme_button = ttk.Button(main_frame, text="Toggle Theme", 
                            command=theme_manager.toggle_theme,
                            style="Primary.TButton")
    theme_button.pack(pady=20)
    
    # Treeview sample
    ttk.Label(main_frame, text="Sample Treeview:").pack(anchor=tk.W, pady=(20, 5))
    tree = ttk.Treeview(main_frame, columns=("name", "value"), show="headings")
    tree.heading("name", text="Name")
    tree.heading("value", text="Value")
    tree.insert("", tk.END, values=("Item 1", "Value 1"))
    tree.insert("", tk.END, values=("Item 2", "Value 2"))
    tree.insert("", tk.END, values=("Item 3", "Value 3"))
    tree.pack(fill=tk.BOTH, expand=True)
    
    root.mainloop()

if __name__ == "__main__":
    main()