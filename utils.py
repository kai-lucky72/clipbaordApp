"""
Utilities Module

This module provides utility functions used across the application.
"""
import os
import sys
import logging
import platform
from datetime import datetime
from pathlib import Path
import hashlib

def setup_logger():
    """
    Configure the application logger.
    """
    # Check if running on Vercel
    if 'VERCEL' in os.environ:
        # On Vercel, only use console logging (no file logging)
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.StreamHandler()
            ]
        )
        
        # Set level for third-party libraries
        for logger_name in ['PIL', 'sqlalchemy.engine']:
            logging.getLogger(logger_name).setLevel(logging.WARNING)
        
        # Log system info
        logger = logging.getLogger(__name__)
        logger.info("Running on Vercel serverless environment")
        logger.info(f"Python: {platform.python_version()}")
        return
    
    # Regular environment (not Vercel)
    # In a server environment like Replit, use the current directory for logs
    if os.environ.get('REPL_ID'):
        log_dir = os.path.join(os.getcwd(), 'logs')
    else:
        # Determine log file path based on platform
        if platform.system() == 'Windows':
            log_dir = os.path.join(os.environ.get('APPDATA', '.'), 'ClipboardManager', 'logs')
        elif platform.system() == 'Darwin':  # macOS
            log_dir = os.path.join(os.path.expanduser('~'), 'Library', 'Logs', 'ClipboardManager')
        else:  # Linux/Unix
            log_dir = os.path.join(os.path.expanduser('~'), '.clipboard_manager', 'logs')
    
    # Create log directory if it doesn't exist
    os.makedirs(log_dir, exist_ok=True)
    
    # Create log file name based on current date
    log_file = os.path.join(log_dir, f"clipboard_manager_{datetime.now().strftime('%Y%m%d')}.log")
    
    # Configure logging
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )
    
    # Set level for third-party libraries
    for logger_name in ['PIL', 'sqlalchemy.engine']:
        logging.getLogger(logger_name).setLevel(logging.WARNING)
    
    # Log system info
    logger = logging.getLogger(__name__)
    logger.info(f"System: {platform.system()} {platform.release()}")
    logger.info(f"Python: {platform.python_version()}")
    logger.info(f"Log file: {log_file}")

def resource_path(relative_path):
    """
    Get absolute path to a resource, works for both development and PyInstaller.
    """
    try:
        # PyInstaller creates a temporary folder and places files there
        # This attribute is injected by PyInstaller at runtime, so it will
        # only exist when running from a packaged executable
        base_path = getattr(sys, '_MEIPASS', None)
        if base_path is None:
            raise AttributeError("_MEIPASS not found")
    except Exception:
        # Running in normal Python environment
        base_path = os.path.abspath(os.path.dirname(sys.argv[0]))
    
    return os.path.join(base_path, relative_path)

def get_system_locale():
    """
    Get the system locale.
    """
    import locale
    system_locale = locale.getdefaultlocale()[0]
    return system_locale or 'en_US'

def get_app_data_dir():
    """
    Get the application data directory based on platform.
    """
    # Check if running on Vercel
    if 'VERCEL' in os.environ:
        # On Vercel, use a temporary directory that doesn't require creation
        return '/tmp'
        
    # Regular environment (not Vercel)
    if platform.system() == 'Windows':
        app_data = os.path.join(os.environ['APPDATA'], 'ClipboardManager')
    elif platform.system() == 'Darwin':  # macOS
        app_data = os.path.join(os.path.expanduser('~'), 'Library', 'Application Support', 'ClipboardManager')
    else:  # Linux/Unix
        app_data = os.path.join(os.path.expanduser('~'), '.clipboard_manager')
    
    # Create directory if it doesn't exist
    os.makedirs(app_data, exist_ok=True)
    return app_data

def format_timestamp(timestamp):
    """
    Format a timestamp for display.
    """
    now = datetime.now()
    delta = now - timestamp
    
    if delta.days == 0:
        return f"Today at {timestamp.strftime('%I:%M %p')}"
    elif delta.days == 1:
        return f"Yesterday at {timestamp.strftime('%I:%M %p')}"
    elif delta.days < 7:
        return timestamp.strftime('%A at %I:%M %p')
    else:
        return timestamp.strftime('%b %d, %Y at %I:%M %p')

def get_image_hash(image_data):
    """
    Generate a hash for image data.
    """
    return hashlib.md5(image_data).hexdigest()

def limit_text_length(text, max_length=50):
    """
    Limit text length and add ellipsis if needed.
    """
    if len(text) > max_length:
        return f"{text[:max_length-3]}..."
    return text
