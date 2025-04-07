"""
Clipboard Manager Module

This module is responsible for monitoring the clipboard for changes
and managing clipboard content (text and images).
"""
import logging
import time
import io
from datetime import datetime
from threading import Thread, Event
from enum import Enum

from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QObject, pyqtSignal, QMimeData, QBuffer, QByteArray
from PyQt5.QtGui import QImage, QPixmap, QGuiApplication
from PIL import Image

from database import DatabaseManager

logger = logging.getLogger(__name__)

class ClipItemType(Enum):
    TEXT = "text"
    IMAGE = "image"

class ClipboardManager(QObject):
    """
    Monitors and manages clipboard operations.
    """
    clipboard_changed = pyqtSignal()
    
    def __init__(self, db_manager):
        super().__init__()
        self.db_manager = db_manager
        self.clipboard = QGuiApplication.clipboard()
        self.clipboard.dataChanged.connect(self._handle_clipboard_change)
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
        # In a real app, load from QSettings or similar
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
        while not self.stop_event.is_set():
            # This is mostly a fallback in case the dataChanged signal misses something
            # Most work is done in _handle_clipboard_change which is connected to the signal
            time.sleep(0.5)  # Sleep to avoid high CPU usage
    
    def _handle_clipboard_change(self):
        """
        Handle clipboard data changes.
        """
        mime_data = self.clipboard.mimeData()
        
        if mime_data.hasText():
            text = mime_data.text()
            # Avoid duplicate entries for the same text
            if text != self.previous_text and text.strip():
                self.previous_text = text
                timestamp = datetime.now()
                self.db_manager.add_clipboard_item(text, ClipItemType.TEXT.value, timestamp)
                logger.debug(f"New text added to clipboard history: {text[:50]}...")
                self.clipboard_changed.emit()
        
        elif mime_data.hasImage() and self.track_images:
            self._handle_clipboard_image(mime_data)
    
    def _handle_clipboard_image(self, mime_data):
        """
        Handle image data from clipboard.
        """
        image = mime_data.imageData()
        if not image:
            return
            
        # Convert QImage to bytes for storage and hashing
        buffer = QBuffer()
        buffer.open(QBuffer.ReadWrite)
        image.save(buffer, "PNG")
        image_bytes = buffer.data().data()
        
        # Generate a simple hash of the image data to avoid duplicates
        import hashlib
        image_hash = hashlib.md5(image_bytes).hexdigest()
        
        if image_hash != self.previous_image_hash:
            self.previous_image_hash = image_hash
            timestamp = datetime.now()
            self.db_manager.add_clipboard_item(image_bytes, ClipItemType.IMAGE.value, timestamp)
            logger.debug(f"New image added to clipboard history (hash: {image_hash})")
            self.clipboard_changed.emit()
    
    def set_clipboard_content(self, clipboard_item):
        """
        Set clipboard content from a database item.
        """
        mime_data = QMimeData()
        
        if clipboard_item['type'] == ClipItemType.TEXT.value:
            mime_data.setText(clipboard_item['content'])
            self.previous_text = clipboard_item['content']
            logger.debug(f"Set clipboard to text: {clipboard_item['content'][:50]}...")
        
        elif clipboard_item['type'] == ClipItemType.IMAGE.value:
            # Convert bytes to QImage
            image = QImage()
            image.loadFromData(clipboard_item['content'])
            mime_data.setImageData(image)
            
            # Update previous image hash
            import hashlib
            self.previous_image_hash = hashlib.md5(clipboard_item['content']).hexdigest()
            logger.debug(f"Set clipboard to image (hash: {self.previous_image_hash})")
        
        # Temporarily disconnect the dataChanged signal to avoid recursion
        self.clipboard.dataChanged.disconnect(self._handle_clipboard_change)
        self.clipboard.setMimeData(mime_data)
        self.clipboard.dataChanged.connect(self._handle_clipboard_change)
