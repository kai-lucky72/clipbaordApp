#!/usr/bin/env python3
"""
Test script for tkinter GUI functionality
"""
import tkinter as tk
from tkinter import ttk
import sys

def main():
    """Test tkinter functionality"""
    print("Starting tkinter test...")
    
    try:
        # Create the main window
        root = tk.Tk()
        root.title("Tkinter Test")
        root.geometry("400x300")
        
        # Add a label
        label = ttk.Label(root, text="Tkinter is working!")
        label.pack(pady=20)
        
        # Add a button
        button = ttk.Button(root, text="Click Me", command=lambda: print("Button clicked!"))
        button.pack(pady=10)
        
        # Add a text entry
        entry = ttk.Entry(root)
        entry.pack(pady=10)
        entry.insert(0, "Sample text")
        
        # Display information about the environment
        info_text = f"Python version: {sys.version}\nTkinter version: {tk.TkVersion}"
        info_label = ttk.Label(root, text=info_text)
        info_label.pack(pady=20)
        
        print("Tkinter window created successfully")
        print(f"Python version: {sys.version}")
        print(f"Tkinter version: {tk.TkVersion}")
        
        # Start the main loop
        root.mainloop()
        
    except Exception as e:
        print(f"Error: {str(e)}")
        return False
    
    return True

if __name__ == "__main__":
    result = main()
    print(f"Test {'successful' if result else 'failed'}")