"""
Database Manager Module

This module handles all database operations for the clipboard manager.
"""
import os
import logging
from datetime import datetime
import json
from enum import Enum
from pathlib import Path
import sqlalchemy
from sqlalchemy import create_engine, Column, Integer, String, LargeBinary, DateTime, Boolean, desc
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

Base = declarative_base()
logger = logging.getLogger(__name__)

class ClipboardItem(Base):
    """SQLAlchemy model for clipboard items"""
    __tablename__ = 'clipboard_items'
    
    id = Column(Integer, primary_key=True)
    content = Column(LargeBinary)  # Store both text and image content as binary
    type = Column(String(10))  # 'text' or 'image'
    timestamp = Column(DateTime, default=datetime.now)
    favorite = Column(Boolean, default=False)
    tags = Column(String)  # Store tags as a JSON string

class DatabaseManager:
    """
    Manages all database operations for the clipboard manager.
    """
    def __init__(self, db_url=None):
        # Use environment variables for PostgreSQL connection if available
        if db_url is None:
            db_url = os.environ.get('DATABASE_URL')
            if not db_url:
                logger.warning("DATABASE_URL not found in environment variables, falling back to SQLite")
                # Use SQLite as fallback
                home_dir = Path.home()
                app_dir = home_dir / ".clipboard_manager"
                app_dir.mkdir(exist_ok=True)
                db_path = app_dir / "clipboard_history.db"
                db_url = f'sqlite:///{db_path}'
        
        try:
            # Initialize SQLAlchemy engine and session
            self.engine = create_engine(db_url)
            Base.metadata.create_all(self.engine)
            self.Session = sessionmaker(bind=self.engine)
            
            logger.info(f"Database initialized successfully using {self.engine.name}")
        except Exception as e:
            logger.error(f"Error initializing database: {e}")
            raise

    def add_clipboard_item(self, content, item_type, timestamp=None):
        """
        Add a new clipboard item to the database.
        
        Args:
            content: The clipboard content (text string or bytes for images)
            item_type: Type of content ('text' or 'image')
            timestamp: Optional timestamp (defaults to current time)
        
        Returns:
            The ID of the newly added item
        """
        session = self.Session()
        try:
            # Convert text to bytes if necessary
            if item_type == 'text' and isinstance(content, str):
                content = content.encode('utf-8')
            
            # Create new item
            new_item = ClipboardItem(
                content=content,
                type=item_type,
                timestamp=timestamp or datetime.now(),
                favorite=False,
                tags=json.dumps([])
            )
            
            session.add(new_item)
            session.commit()
            item_id = new_item.id
            logger.debug(f"Added new {item_type} item to database, ID: {item_id}")
            return item_id
        except Exception as e:
            session.rollback()
            logger.error(f"Error adding clipboard item: {e}")
            raise
        finally:
            session.close()

    def get_recent_items(self, limit=5):
        """
        Get the most recent clipboard items.
        
        Args:
            limit: Maximum number of items to return (default 5)
            
        Returns:
            List of dictionaries containing clipboard items
        """
        session = self.Session()
        try:
            items = session.query(ClipboardItem).order_by(
                desc(ClipboardItem.timestamp)).limit(limit).all()
            
            result = []
            for item in items:
                # Keep binary content as is for CLI version
                result.append({
                    'id': item.id,
                    'content': item.content,
                    'type': item.type,
                    'timestamp': item.timestamp,
                    'favorite': item.favorite,
                    'tags': json.loads(item.tags or '[]')
                })
            
            return result
        except Exception as e:
            logger.error(f"Error retrieving recent items: {e}")
            return []
        finally:
            session.close()

    def get_all_items(self, search_text=None, filter_type=None, favorites_only=False):
        """
        Get all clipboard items with optional filtering.
        
        Args:
            search_text: Optional text to search for
            filter_type: Optional filter by item type ('text' or 'image')
            favorites_only: If True, only return favorite items
            
        Returns:
            List of dictionaries containing clipboard items
        """
        session = self.Session()
        try:
            query = session.query(ClipboardItem)
            
            # Apply filters
            if search_text and search_text.strip():
                # PostgreSQL requires different approach for bytea search
                if self.engine.name == 'postgresql':
                    # Using the position function for PostgreSQL binary search
                    search_bytes = search_text.encode('utf-8')
                    query = query.filter(
                        ClipboardItem.type == 'text',
                        # Use SQL expression to cast and search within content
                        sqlalchemy.text(f"position('{search_bytes.hex()}' in encode(content, 'hex')) > 0")
                    )
                else:
                    # SQLite approach
                    query = query.filter(
                        ClipboardItem.type == 'text',
                        ClipboardItem.content.like(f'%{search_text.encode("utf-8")}%')
                    )
            
            if filter_type:
                query = query.filter(ClipboardItem.type == filter_type)
                
            if favorites_only:
                query = query.filter(ClipboardItem.favorite == True)
            
            # Order by timestamp, newest first
            query = query.order_by(desc(ClipboardItem.timestamp))
            
            items = query.all()
            
            result = []
            for item in items:
                # Keep binary content as is for CLI version
                result.append({
                    'id': item.id,
                    'content': item.content,
                    'type': item.type,
                    'timestamp': item.timestamp,
                    'favorite': item.favorite,
                    'tags': json.loads(item.tags or '[]')
                })
            
            return result
        except Exception as e:
            logger.error(f"Error retrieving items: {e}")
            return []
        finally:
            session.close()

    def get_item_by_id(self, item_id):
        """
        Get a specific clipboard item by ID.
        
        Args:
            item_id: The ID of the item to retrieve
            
        Returns:
            Dictionary containing the clipboard item or None if not found
        """
        session = self.Session()
        try:
            item = session.query(ClipboardItem).filter(ClipboardItem.id == item_id).first()
            
            if not item:
                return None
            
            # Keep binary content as is for CLI version
            return {
                'id': item.id,
                'content': item.content,
                'type': item.type,
                'timestamp': item.timestamp,
                'favorite': item.favorite,
                'tags': json.loads(item.tags or '[]')
            }
        except Exception as e:
            logger.error(f"Error retrieving item {item_id}: {e}")
            return None
        finally:
            session.close()

    def delete_item(self, item_id):
        """
        Delete a clipboard item by ID.
        
        Args:
            item_id: The ID of the item to delete
            
        Returns:
            True if successful, False otherwise
        """
        session = self.Session()
        try:
            item = session.query(ClipboardItem).filter(ClipboardItem.id == item_id).first()
            if item:
                session.delete(item)
                session.commit()
                logger.debug(f"Deleted clipboard item {item_id}")
                return True
            return False
        except Exception as e:
            session.rollback()
            logger.error(f"Error deleting item {item_id}: {e}")
            return False
        finally:
            session.close()

    def toggle_favorite(self, item_id):
        """
        Toggle the favorite status of a clipboard item.
        
        Args:
            item_id: The ID of the item to update
            
        Returns:
            The new favorite status if successful, None otherwise
        """
        session = self.Session()
        try:
            item = session.query(ClipboardItem).filter(ClipboardItem.id == item_id).first()
            if item:
                item.favorite = not item.favorite
                session.commit()
                logger.debug(f"Updated favorite status for item {item_id} to {item.favorite}")
                return item.favorite
            return None
        except Exception as e:
            session.rollback()
            logger.error(f"Error toggling favorite for item {item_id}: {e}")
            return None
        finally:
            session.close()

    def add_tag(self, item_id, tag):
        """
        Add a tag to a clipboard item.
        
        Args:
            item_id: The ID of the item to tag
            tag: The tag to add
            
        Returns:
            List of current tags if successful, None otherwise
        """
        session = self.Session()
        try:
            item = session.query(ClipboardItem).filter(ClipboardItem.id == item_id).first()
            if item:
                tags = json.loads(item.tags or '[]')
                if tag not in tags:
                    tags.append(tag)
                    item.tags = json.dumps(tags)
                    session.commit()
                    logger.debug(f"Added tag '{tag}' to item {item_id}")
                return tags
            return None
        except Exception as e:
            session.rollback()
            logger.error(f"Error adding tag to item {item_id}: {e}")
            return None
        finally:
            session.close()

    def remove_tag(self, item_id, tag):
        """
        Remove a tag from a clipboard item.
        
        Args:
            item_id: The ID of the item
            tag: The tag to remove
            
        Returns:
            List of current tags if successful, None otherwise
        """
        session = self.Session()
        try:
            item = session.query(ClipboardItem).filter(ClipboardItem.id == item_id).first()
            if item:
                tags = json.loads(item.tags or '[]')
                if tag in tags:
                    tags.remove(tag)
                    item.tags = json.dumps(tags)
                    session.commit()
                    logger.debug(f"Removed tag '{tag}' from item {item_id}")
                return tags
            return None
        except Exception as e:
            session.rollback()
            logger.error(f"Error removing tag from item {item_id}: {e}")
            return None
        finally:
            session.close()

    def clear_history(self, keep_favorites=True):
        """
        Clear clipboard history.
        
        Args:
            keep_favorites: If True, favorite items will not be deleted
            
        Returns:
            Number of items deleted
        """
        session = self.Session()
        try:
            query = session.query(ClipboardItem)
            if keep_favorites:
                query = query.filter(ClipboardItem.favorite == False)
            
            count = query.count()
            query.delete(synchronize_session=False)
            session.commit()
            
            logger.info(f"Cleared clipboard history, {count} items deleted")
            return count
        except Exception as e:
            session.rollback()
            logger.error(f"Error clearing history: {e}")
            return 0
        finally:
            session.close()
