#!/usr/bin/env python3
"""
Database Connection Test Script

This script tests the database connection and tables.
It's useful for debugging database issues, especially in Vercel.
"""
import os
import sys
import logging
import traceback
from datetime import datetime

# Basic logging setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("db_test")

# Import vercel setup to configure environment
try:
    import vercel_setup
    vercel_setup.setup_vercel_environment()
    logger.info("Vercel environment setup complete")
except ImportError:
    logger.info("Not in Vercel environment (vercel_setup not imported)")
except Exception as e:
    logger.error(f"Error in Vercel setup: {e}")

# Check for DATABASE_URL environment variable
db_url = os.environ.get('DATABASE_URL')
if db_url:
    # Mask password for security in logs
    if '://' in db_url:
        parts = db_url.split('://')
        if '@' in parts[1]:
            auth_part = parts[1].split('@')[0]
            if ':' in auth_part:
                user = auth_part.split(':')[0]
                masked_url = f"{parts[0]}://{user}:****@{parts[1].split('@')[1]}"
                logger.info(f"DATABASE_URL format: {masked_url}")
            else:
                logger.info("DATABASE_URL provided (no password in URL)")
        else:
            logger.info("DATABASE_URL provided (no auth in URL)")
    else:
        logger.info("DATABASE_URL provided (unusual format)")
else:
    logger.error("No DATABASE_URL found in environment")
    sys.exit(1)

# Try to import SQLAlchemy
try:
    import sqlalchemy
    from sqlalchemy import create_engine, text
    logger.info(f"SQLAlchemy version: {sqlalchemy.__version__}")
except ImportError:
    logger.error("SQLAlchemy is not installed. Install with: pip install sqlalchemy")
    sys.exit(1)

def test_connection():
    """Test basic database connection"""
    try:
        logger.info("Testing database connection...")
        
        # Fix PostgreSQL URL format if needed
        if db_url.startswith('postgres://'):
            fixed_db_url = db_url.replace('postgres://', 'postgresql://', 1)
            logger.info("Fixed database URL format (postgres:// -> postgresql://)")
        else:
            fixed_db_url = db_url
        
        # Create engine with logging
        engine = create_engine(fixed_db_url, echo=True)
        
        # Try to connect and execute a simple query
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            logger.info(f"Connection successful: {result.scalar()}")
            
            # Get database info
            db_info = conn.execute(text("SELECT version()")).scalar()
            logger.info(f"Database info: {db_info}")
            
            # List all tables
            logger.info("Listing all tables:")
            tables_query = text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema='public'
            """)
            tables = [row[0] for row in conn.execute(tables_query)]
            
            if not tables:
                logger.warning("No tables found in the database")
            else:
                logger.info(f"Tables found: {', '.join(tables)}")
                
                # Check for clipboard_items table
                if 'clipboard_items' in tables:
                    logger.info("Found clipboard_items table, checking structure...")
                    columns_query = text("""
                        SELECT column_name, data_type 
                        FROM information_schema.columns 
                        WHERE table_name = 'clipboard_items'
                    """)
                    columns = [(row[0], row[1]) for row in conn.execute(columns_query)]
                    for col_name, col_type in columns:
                        logger.info(f"  - {col_name}: {col_type}")
                    
                    # Count items
                    count_query = text("SELECT COUNT(*) FROM clipboard_items")
                    count = conn.execute(count_query).scalar()
                    logger.info(f"Total clipboard items: {count}")
                    
                    # Get a sample item if any exist
                    if count > 0:
                        sample_query = text("SELECT id, type, timestamp, favorite FROM clipboard_items LIMIT 1")
                        sample = conn.execute(sample_query).fetchone()
                        logger.info(f"Sample item: {sample}")
                else:
                    logger.warning("clipboard_items table not found")
            
        logger.info("Database test completed successfully")
        return True
        
    except Exception as e:
        logger.error(f"Database connection error: {str(e)}")
        logger.error(traceback.format_exc())
        return False

if __name__ == "__main__":
    success = test_connection()
    sys.exit(0 if success else 1)