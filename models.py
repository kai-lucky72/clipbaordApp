"""
Models Module

This module defines data models used throughout the application.
"""
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import List, Optional, Any

class ClipItemType(Enum):
    TEXT = "text"
    IMAGE = "image"

@dataclass
class ClipboardItem:
    """
    Represents a clipboard item.
    """
    id: int
    content: Any  # Text string or bytes for images
    type: str  # 'text' or 'image'
    timestamp: datetime
    favorite: bool = False
    tags: List[str] = None
    
    def __post_init__(self):
        if self.tags is None:
            self.tags = []
    
    @property
    def formatted_timestamp(self) -> str:
        """
        Returns a nicely formatted timestamp string.
        """
        now = datetime.now()
        delta = now - self.timestamp
        
        # Today
        if delta.days == 0:
            return f"Today at {self.timestamp.strftime('%I:%M %p')}"
        # Yesterday
        elif delta.days == 1:
            return f"Yesterday at {self.timestamp.strftime('%I:%M %p')}"
        # Within the last week
        elif delta.days < 7:
            return self.timestamp.strftime('%A at %I:%M %p')
        # Older
        else:
            return self.timestamp.strftime('%b %d, %Y at %I:%M %p')
    
    @property
    def preview(self) -> str:
        """
        Returns a preview of the content.
        For text, returns the first 100 characters.
        For images, returns a descriptive string.
        """
        if self.type == ClipItemType.TEXT.value:
            text = self.content
            if len(text) > 100:
                return f"{text[:97]}..."
            return text
        else:
            return f"[Image - {self.formatted_timestamp}]"

@dataclass
class AppSettings:
    """
    Application settings.
    """
    track_images: bool = True
    start_with_os: bool = False
    start_minimized: bool = True
    show_notifications: bool = True
    max_history_items: int = 1000
    theme: str = "light"
    enable_encryption: bool = False
    encryption_key: Optional[str] = None
