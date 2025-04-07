"""
Clipboard Manager Module

This module is responsible for monitoring the clipboard for changes
and managing clipboard content (text and images) in a CLI environment.
"""
import logging
import time
import io
import hashlib
from datetime import datetime
from threading import Thread, Event
from enum import Enum

from database import DatabaseManager

logger = logging.getLogger(__name__)

class ClipItemType(Enum):
    TEXT = "text"
    IMAGE = "image"

class ClipboardManager:
    """
    Monitors and manages clipboard operations in a CLI environment.
    """
    
    def __init__(self, db_manager):
        self.db_manager = db_manager
        self.stop_event = Event()
        self.monitoring_thread = None
        self.track_images = True  # Can be toggled in settings
        self.previous_text = ""
        self.previous_image_hash = None
        
        # Load settings
        self.load_settings()
    
    def load_settings(self):
        """
        Load clipboard manager settings.
        """
        # In a real app, load from config file or database
        # For now, set defaults
        self.track_images = True
    
    def set_track_images(self, track_images):
        """
        Enable or disable image tracking.
        """
        self.track_images = track_images
        logger.info(f"Image tracking set to: {track_images}")
    
    def start_monitoring(self):
        """
        Start the clipboard monitoring service.
        """
        if self.monitoring_thread is not None and self.monitoring_thread.is_alive():
            logger.warning("Clipboard monitoring already running")
            return
        
        self.stop_event.clear()
        self.monitoring_thread = Thread(target=self._monitor_clipboard, daemon=True)
        self.monitoring_thread.start()
        logger.info("Clipboard monitoring started")
    
    def stop_monitoring(self):
        """
        Stop the clipboard monitoring service.
        """
        if self.monitoring_thread is None or not self.monitoring_thread.is_alive():
            logger.warning("Clipboard monitoring not running")
            return
            
        self.stop_event.set()
        self.monitoring_thread.join(timeout=1.0)
        logger.info("Clipboard monitoring stopped")
    
    def _monitor_clipboard(self):
        """
        Background thread for monitoring clipboard changes.
        """
        try:
            # Try to use pyperclip for cross-platform clipboard access
            import pyperclip
            have_pyperclip = True
        except ImportError:
            have_pyperclip = False
            logger.warning("pyperclip not available, using in-memory clipboard only")
            
        last_text = None
        
        while not self.stop_event.is_set():
            try:
                if have_pyperclip:
                    # Get current clipboard text
                    try:
                        current_text = pyperclip.paste()
                        if current_text and current_text != last_text:
                            # Avoid duplicate entries for the same text
                            last_text = current_text
                            timestamp = datetime.now()
                            item_id = self.db_manager.add_clipboard_item(current_text.encode('utf-8'), ClipItemType.TEXT.value, timestamp)
                            logger.debug(f"New text added to clipboard history: {current_text[:50]}...")
                    except Exception as e:
                        logger.error(f"Error getting clipboard content: {e}")
            except Exception as e:
                logger.error(f"Error in clipboard monitoring: {e}")
                
            # Sleep to avoid high CPU usage
            time.sleep(1.0)
    
    def add_text_to_clipboard(self, text):
        """
        Add text to the clipboard and database.
        
        Args:
            text: The text to add
            
        Returns:
            The ID of the added item
        """
        if not text or text == self.previous_text:
            return None
            
        self.previous_text = text
        timestamp = datetime.now()
        item_id = self.db_manager.add_clipboard_item(text.encode('utf-8'), ClipItemType.TEXT.value, timestamp)
        
        # Try to set system clipboard if pyperclip is available
        try:
            import pyperclip
            pyperclip.copy(text)
            logger.debug(f"Text set to system clipboard: {text[:50]}...")
        except ImportError:
            logger.debug("pyperclip not available, content stored in database only")
        except Exception as e:
            logger.error(f"Error setting system clipboard: {e}")
            
        return item_id
    
    def add_image_to_clipboard(self, image_bytes):
        """
        Add image to the clipboard and database.
        
        Args:
            image_bytes: The binary image data
            
        Returns:
            The ID of the added item
        """
        if not self.track_images or not image_bytes:
            return None
            
        # Generate a hash of the image data to avoid duplicates
        image_hash = hashlib.md5(image_bytes).hexdigest()
        
        if image_hash == self.previous_image_hash:
            return None
            
        self.previous_image_hash = image_hash
        timestamp = datetime.now()
        item_id = self.db_manager.add_clipboard_item(image_bytes, ClipItemType.IMAGE.value, timestamp)
        logger.debug(f"New image added to clipboard history (hash: {image_hash})")
        
        # Note: Setting image to system clipboard requires GUI libraries
        # in CLI mode, we just store it in the database
        
        return item_id
    
    def get_clipboard_content(self, clipboard_item):
        """
        Get clipboard content from a database item.
        
        Args:
            clipboard_item: The database item
            
        Returns:
            The content as text or bytes
        """
        if not clipboard_item or 'content' not in clipboard_item or clipboard_item['content'] is None:
            logger.warning("Invalid clipboard item or missing content")
            return None
            
        if clipboard_item['type'] == ClipItemType.TEXT.value:
            try:
                content = clipboard_item['content'].decode('utf-8', errors='replace')
                # Try to set system clipboard if pyperclip is available
                try:
                    import pyperclip
                    pyperclip.copy(content)
                    logger.debug(f"Text set to system clipboard: {content[:50]}...")
                except ImportError:
                    logger.debug("pyperclip not available, content returned only")
                except Exception as e:
                    logger.error(f"Error setting system clipboard: {e}")
                return content
            except Exception as e:
                logger.error(f"Error decoding text content: {e}")
                return None
        
        elif clipboard_item['type'] == ClipItemType.IMAGE.value:
            # In CLI mode, we can't display images directly
            # Just return the binary data
            return clipboard_item['content']
        
        return None
