#!/usr/bin/env python3
"""
Keyboard Handler Module

This module handles global keyboard shortcuts for the clipboard manager.
It uses a platform-independent approach to catch key combinations.
"""
import os
import sys
import threading
import time
import logging

# Configure logging
logger = logging.getLogger(__name__)

class KeyboardHandler:
    """
    Handles global keyboard shortcuts for the clipboard manager
    """
    
    def __init__(self, callback=None):
        """
        Initialize the keyboard handler
        
        Args:
            callback: Function to call when shortcut is triggered
        """
        self.callback = callback
        self.monitoring = False
        self.monitor_thread = None
        
        # Platform-specific setup
        self.platform = sys.platform
    
    def start_monitoring(self):
        """Start monitoring keyboard shortcuts"""
        if self.monitoring:
            return
            
        self.monitoring = True
        self.monitor_thread = threading.Thread(target=self._monitor_keyboard, daemon=True)
        self.monitor_thread.start()
        logger.info("Keyboard shortcut monitoring started")
    
    def stop_monitoring(self):
        """Stop monitoring keyboard shortcuts"""
        self.monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=1.0)
        logger.info("Keyboard shortcut monitoring stopped")
    
    def _monitor_keyboard(self):
        """Background thread for monitoring keyboard shortcuts"""
        try:
            if self.platform == 'win32':
                self._monitor_windows_keyboard()
            elif self.platform == 'darwin':
                self._monitor_macos_keyboard()
            else:
                self._monitor_linux_keyboard()
        except Exception as e:
            logger.error(f"Error in keyboard monitoring: {e}")
            self.monitoring = False
    
    def _monitor_windows_keyboard(self):
        """Monitor keyboard shortcuts on Windows"""
        try:
            # Use win32api if available
            import win32api
            import win32con
            
            logger.info("Using win32api for keyboard monitoring")
            
            def check_keyboard():
                # Check Ctrl+Shift+V
                ctrl_state = win32api.GetAsyncKeyState(win32con.VK_CONTROL)
                shift_state = win32api.GetAsyncKeyState(win32con.VK_SHIFT)
                v_state = win32api.GetAsyncKeyState(ord('V'))
                
                if (ctrl_state & 0x8000) and (shift_state & 0x8000) and (v_state & 0x8000):
                    # Shortcut detected - wait for key release to avoid multiple triggers
                    while (win32api.GetAsyncKeyState(ord('V')) & 0x8000):
                        time.sleep(0.01)
                    
                    if self.callback:
                        self.callback()
            
            # Main monitoring loop
            while self.monitoring:
                check_keyboard()
                time.sleep(0.1)  # Check every 100ms
                
        except ImportError:
            logger.warning("win32api not available, falling back to basic method")
            self._monitor_basic_keyboard()
    
    def _monitor_macos_keyboard(self):
        """Monitor keyboard shortcuts on macOS"""
        try:
            # Try to use pynput if available
            from pynput import keyboard
            
            logger.info("Using pynput for keyboard monitoring")
            
            # Create a flag to track if keys are pressed to avoid duplicate events
            hotkey_active = False
            
            def on_press(key):
                nonlocal hotkey_active
                if not hotkey_active and hasattr(key, 'char') and key.char == 'v':
                    # Check if cmd and shift are also pressed on macOS
                    if keyboard.Key.cmd in pressed_keys and keyboard.Key.shift in pressed_keys:
                        hotkey_active = True
                        if self.callback:
                            self.callback()
            
            def on_release(key):
                nonlocal hotkey_active
                if key == keyboard.KeyCode.from_char('v'):
                    hotkey_active = False
            
            # Create a set of currently pressed keys
            pressed_keys = set()
            
            # Define the listeners
            with keyboard.Listener(
                on_press=on_press,
                on_release=on_release
            ) as listener:
                listener.join()
                
        except ImportError:
            logger.warning("pynput not available, falling back to basic method")
            self._monitor_basic_keyboard()
    
    def _monitor_linux_keyboard(self):
        """Monitor keyboard shortcuts on Linux"""
        try:
            # Try to use pynput if available
            from pynput import keyboard
            
            logger.info("Using pynput for keyboard monitoring")
            
            # Create a flag to track if keys are pressed to avoid duplicate events
            hotkey_active = False
            
            def on_press(key):
                nonlocal hotkey_active
                if not hotkey_active and hasattr(key, 'char') and key.char == 'v':
                    # Check if ctrl and shift are also pressed on Linux
                    if keyboard.Key.ctrl in pressed_keys and keyboard.Key.shift in pressed_keys:
                        hotkey_active = True
                        if self.callback:
                            self.callback()
            
            def on_release(key):
                nonlocal hotkey_active
                if key == keyboard.KeyCode.from_char('v'):
                    hotkey_active = False
            
            # Create a set of currently pressed keys
            pressed_keys = set()
            
            # Define the listeners
            with keyboard.Listener(
                on_press=on_press,
                on_release=on_release
            ) as listener:
                listener.join()
                
        except ImportError:
            logger.warning("pynput not available, falling back to basic method")
            self._monitor_basic_keyboard()
    
    def _monitor_basic_keyboard(self):
        """
        Basic fallback method for keyboard monitoring
        
        Note: This is not very reliable but serves as a fallback
        when platform-specific methods are not available
        """
        logger.info("Using basic keyboard monitoring (limited functionality)")
        
        # Simple polling loop - this is a very limited approach
        # and will only work when the application has focus
        while self.monitoring:
            # TODO: Implement a basic keyboard polling mechanism
            # For now, just sleep to avoid CPU usage
            time.sleep(0.5)


def main():
    """Standalone test function"""
    import signal
    
    def signal_handler(sig, frame):
        print("\nExiting keyboard handler")
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    
    def on_shortcut_triggered():
        print("Shortcut triggered!")
    
    handler = KeyboardHandler(callback=on_shortcut_triggered)
    handler.start_monitoring()
    
    print("Keyboard handler started. Press Ctrl+Shift+V to test (Cmd+Shift+V on macOS).")
    print("Press Ctrl+C to exit.")
    
    # Keep the main thread alive
    while True:
        time.sleep(1)

if __name__ == "__main__":
    main()