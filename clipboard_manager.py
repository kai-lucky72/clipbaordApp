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
from clipboard_adapter import ClipboardAdapter

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
        last_text = None
        last_image_hash = None
        
        while not self.stop_event.is_set():
            try:
                # Get current clipboard text using our adapter
                current_text = ClipboardAdapter.get_text()
                if current_text and current_text != last_text:
                    # Avoid duplicate entries for the same text
                    last_text = current_text
                    timestamp = datetime.now()
                    item_id = self.db_manager.add_clipboard_item(current_text.encode('utf-8'), ClipItemType.TEXT.value, timestamp)
                    logger.debug(f"New text added to clipboard history: {current_text[:50]}...")
                
                # Also check for images if tracking is enabled
                if self.track_images:
                    try:
                        image_data = ClipboardAdapter.get_image()
                        if image_data:
                            # Generate hash to avoid duplicates
                            image_hash = hashlib.md5(image_data).hexdigest()
                            if image_hash != last_image_hash:
                                last_image_hash = image_hash
                                timestamp = datetime.now()
                                item_id = self.db_manager.add_clipboard_item(image_data, ClipItemType.IMAGE.value, timestamp)
                                logger.debug(f"New image added to clipboard history (hash: {image_hash})")
                    except Exception as e:
                        logger.error(f"Error processing clipboard image: {e}")
                        
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
        
        # Try to set system clipboard using our adapter
        if ClipboardAdapter.set_text(text):
            logger.debug(f"Text set to system clipboard: {text[:50]}...")
        else:
            logger.debug("Failed to set text to system clipboard, content stored in database only")
            
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
        
        # Try to set the image to system clipboard
        if ClipboardAdapter.set_image(image_bytes):
            logger.debug(f"Image set to system clipboard (hash: {image_hash})")
        else:
            logger.debug("Failed to set image to system clipboard, content stored in database only")
        
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
                # Try to set system clipboard using our adapter
                if ClipboardAdapter.set_text(content):
                    logger.debug(f"Text set to system clipboard: {content[:50]}...")
                else:
                    logger.debug("Failed to set text to system clipboard, content returned only")
                return content
            except Exception as e:
                logger.error(f"Error decoding text content: {e}")
                return None
        
        elif clipboard_item['type'] == ClipItemType.IMAGE.value:
            # Try to set image to system clipboard
            if ClipboardAdapter.set_image(clipboard_item['content']):
                logger.debug("Image set to system clipboard")
            else:
                logger.debug("Failed to set image to system clipboard")
                
            # Return the binary data
            return clipboard_item['content']
        
        return None
