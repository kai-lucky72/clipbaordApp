import vercel_setup
vercel_setup.setup_vercel_environment()
#!/usr/bin/env python3
"""
Web Application Interface for Advanced Clipboard Manager

This module provides a web-based interface to the clipboard manager,
allowing users to access their clipboard history from any browser.
"""
import os
import logging
import json
import traceback
from datetime import datetime
from flask import Flask, render_template, request, jsonify, redirect, url_for, send_file
from io import BytesIO
import base64

# Import SQLAlchemy for better error handling
try:
    import sqlalchemy
    from sqlalchemy.exc import SQLAlchemyError, OperationalError, DatabaseError
    HAS_SQLALCHEMY = True
except ImportError:
    HAS_SQLALCHEMY = False
    # Define mock classes for type checking if SQLAlchemy isn't available
    class SQLAlchemyError(Exception): pass
    class OperationalError(SQLAlchemyError): pass
    class DatabaseError(SQLAlchemyError): pass

from database import DatabaseManager
from clipboard_manager import ClipboardManager, ClipItemType
from utils import setup_logger, limit_text_length, format_timestamp

# Configure logging
setup_logger()
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__, 
           static_folder='web/static', 
           template_folder='web/templates')
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "clipboard_manager_secret_key")

# Initialize database and clipboard manager
# Check if running on Vercel
is_vercel = os.environ.get('VERCEL', '') == 'true' or os.environ.get('VERCEL_URL', '')
db_url = os.environ.get('DATABASE_URL')

# Log database URL (masked for security)
if db_url:
    # Only log a masked version
    if '://' in db_url:
        parts = db_url.split('://')
        if '@' in parts[1]:
            auth_part = parts[1].split('@')[0]
            if ':' in auth_part:
                user = auth_part.split(':')[0]
                masked_url = f"{parts[0]}://{user}:****@{parts[1].split('@')[1]}"
                logger.info(f"Using DATABASE_URL: {masked_url}")
            else:
                logger.info("Using DATABASE_URL (no password in URL)")
        else:
            logger.info("Using DATABASE_URL (no auth in URL)")
    else:
        logger.info("Using DATABASE_URL (unusual format)")
else:
    logger.warning("No DATABASE_URL found in environment. Database connections may fail.")

try:
    logger.info("Initializing database manager...")
    db_manager = DatabaseManager()
    logger.info("Database manager initialized successfully")
    
    # Only initialize clipboard manager in non-serverless environments
    # In serverless environments like Vercel, we don't want to monitor the clipboard
    if not is_vercel:
        logger.info("Initializing clipboard manager...")
        clipboard_manager = ClipboardManager(db_manager)
        logger.info("Clipboard manager initialized successfully")
    else:
        # In Vercel, we only use the web interface without clipboard monitoring
        logger.info("Running on Vercel - clipboard monitoring disabled")
        clipboard_manager = None
except Exception as e:
    logger.error(f"Error initializing database or clipboard manager: {e}")
    logger.error(f"Stack trace: {traceback.format_exc()}")
    
    # Log more detailed error info based on exception type
    if HAS_SQLALCHEMY and isinstance(e, OperationalError):
        logger.error(f"Database connection failed. Check your connection string and credentials.")
        if db_url and 'postgresql' not in db_url and 'postgres' in db_url:
            logger.error("Your DATABASE_URL may be using 'postgres://' instead of 'postgresql://' - SQLAlchemy requires 'postgresql://'")
    
    # In production/Vercel, continue with limited functionality
    if is_vercel:
        logger.warning("Continuing with limited functionality in Vercel environment")
        db_manager = None
        clipboard_manager = None
    else:
        # In development, re-raise the exception to fail fast
        raise

@app.route('/')
def index():
    """Render the main page"""
    # If we're in limited mode due to DB connection failure, 
    # we should show an error message
    if db_manager is None:
        error_message = "Database connection is not available. Please check your configuration."
        return render_template('error.html', error=error_message)
    return render_template('index.html')

@app.route('/api/items')
def get_items():
    """Get clipboard items with optional filtering"""
    # Check if database is available
    if db_manager is None:
        return jsonify({
            'error': 'Database connection is not available',
            'message': 'Please check your DATABASE_URL environment variable',
        }), 503  # Service Unavailable

    filter_type = request.args.get('filter', 'all')
    search_text = request.args.get('search', '')
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 50))
    
    # Convert filter type to expected format
    db_filter = None
    favorites_only = False
    
    if filter_type == 'text':
        db_filter = ClipItemType.TEXT.value
    elif filter_type == 'image':
        db_filter = ClipItemType.IMAGE.value
    elif filter_type == 'favorites':
        favorites_only = True
    
    try:
        # Get items from database
        items = db_manager.get_all_items(
            search_text=search_text,
            filter_type=db_filter,
            favorites_only=favorites_only
        )
        
        # Simple pagination
        total_items = len(items)
        start_idx = (page - 1) * per_page
        end_idx = start_idx + per_page
        items_page = items[start_idx:end_idx]
        
        # Process items for API response
        processed_items = []
        for item in items_page:
            processed_item = {
                'id': item.get('id'),
                'type': item.get('type'),
                'timestamp': format_timestamp(item.get('timestamp')),
                'favorite': item.get('favorite', False),
                'tags': item.get('tags') if isinstance(item.get('tags'), list) else []
            }
            
            # Add content preview
            if item.get('type') == ClipItemType.TEXT.value:
                try:
                    text_content = item['content'].decode('utf-8', errors='replace')
                    processed_item['preview'] = limit_text_length(text_content, 100)
                    processed_item['content'] = text_content
                except Exception as e:
                    processed_item['preview'] = f"[Error: {str(e)}]"
                    processed_item['content'] = ""
            else:
                processed_item['preview'] = "[IMAGE]"
                # For images, create a base64 data URL for display
                try:
                    image_data = item['content']
                    b64_image = base64.b64encode(image_data).decode('utf-8')
                    processed_item['image_data'] = f"data:image/png;base64,{b64_image}"
                except Exception as e:
                    logger.error(f"Error processing image: {e}")
                    processed_item['image_data'] = ""
                    
            processed_items.append(processed_item)
        
        return jsonify({
            'items': processed_items,
            'total': total_items,
            'page': page,
            'per_page': per_page,
            'total_pages': (total_items + per_page - 1) // per_page
        })
    except Exception as e:
        logger.error(f"Error retrieving items: {e}")
        return jsonify({
            'error': 'Database error',
            'message': str(e)
        }), 500

@app.route('/api/item/<int:item_id>')
def get_item(item_id):
    """Get a specific clipboard item"""
    # Check if database is available
    if db_manager is None:
        return jsonify({
            'error': 'Database connection is not available',
            'message': 'Please check your DATABASE_URL environment variable',
        }), 503  # Service Unavailable
        
    try:
        item = db_manager.get_item_by_id(item_id)
        
        if not item:
            return jsonify({'error': 'Item not found'}), 404
            
        processed_item = {
            'id': item.get('id'),
            'type': item.get('type'),
            'timestamp': format_timestamp(item.get('timestamp')),
            'favorite': item.get('favorite', False),
            'tags': item.get('tags') if isinstance(item.get('tags'), list) else []
        }
        
        # Add content based on type
        if item.get('type') == ClipItemType.TEXT.value:
            try:
                text_content = item['content'].decode('utf-8', errors='replace')
                processed_item['content'] = text_content
            except Exception as e:
                processed_item['content'] = f"[Error: {str(e)}]"
        else:
            # For images, create a base64 data URL
            try:
                image_data = item['content']
                b64_image = base64.b64encode(image_data).decode('utf-8')
                processed_item['image_data'] = f"data:image/png;base64,{b64_image}"
            except Exception as e:
                logger.error(f"Error processing image: {e}")
                processed_item['image_data'] = ""
        
        return jsonify(processed_item)
    except Exception as e:
        logger.error(f"Error retrieving item {item_id}: {e}")
        return jsonify({
            'error': 'Database error',
            'message': str(e)
        }), 500

@app.route('/api/item/<int:item_id>/favorite', methods=['POST'])
def toggle_favorite(item_id):
    """Toggle favorite status for an item"""
    result = db_manager.toggle_favorite(item_id)
    
    if result is not None:
        return jsonify({'success': True, 'favorite': result})
    else:
        return jsonify({'error': 'Failed to update favorite status'}), 500

@app.route('/api/item/<int:item_id>/tags', methods=['GET'])
def get_item_tags(item_id):
    """Get tags for an item"""
    item = db_manager.get_item_by_id(item_id)
    
    if not item:
        return jsonify({'error': 'Item not found'}), 404
        
    try:
        tags = item.get('tags')
        if isinstance(tags, list):
            return jsonify({'tags': tags})
        else:
            tags = json.loads(tags or '[]')
            return jsonify({'tags': tags})
    except Exception as e:
        logger.error(f"Error parsing tags: {e}")
        return jsonify({'error': 'Failed to parse tags'}), 500

@app.route('/api/item/<int:item_id>/tags', methods=['POST'])
def add_tag(item_id):
    """Add a tag to an item"""
    tag = request.json.get('tag')
    
    if not tag:
        return jsonify({'error': 'Tag is required'}), 400
        
    result = db_manager.add_tag(item_id, tag)
    
    if result:
        return jsonify({'success': True, 'tags': result})
    else:
        return jsonify({'error': 'Failed to add tag'}), 500

@app.route('/api/item/<int:item_id>/tags/<tag>', methods=['DELETE'])
def remove_tag(item_id, tag):
    """Remove a tag from an item"""
    result = db_manager.remove_tag(item_id, tag)
    
    if result is not None:
        return jsonify({'success': True, 'tags': result})
    else:
        return jsonify({'error': 'Failed to remove tag'}), 500

@app.route('/api/tags')
def get_all_tags():
    """Get all tags used in the system"""
    all_items = db_manager.get_all_items()
    all_tags = set()
    
    for item in all_items:
        if 'tags' in item and item['tags']:
            try:
                if isinstance(item['tags'], list):
                    all_tags.update(item['tags'])
                else:
                    tags = json.loads(item['tags'])
                    all_tags.update(tags)
            except Exception as e:
                logger.error(f"Error parsing tags: {e}")
    
    return jsonify({'tags': sorted(list(all_tags))})

@app.route('/api/items/clear', methods=['POST'])
def clear_history():
    """Clear clipboard history"""
    keep_favorites = request.json.get('keep_favorites', True)
    
    count = db_manager.clear_history(keep_favorites=keep_favorites)
    
    return jsonify({'success': True, 'deleted_count': count})

@app.route('/api/items/add', methods=['POST'])
def add_text():
    """Add text directly to clipboard history"""
    text = request.json.get('text')
    
    if not text:
        return jsonify({'error': 'Text is required'}), 400
    
    # In vercel environment, directly use database manager to add text
    # since clipboard_manager might be None
    if clipboard_manager is None:
        if db_manager is None:
            return jsonify({
                'error': 'Database connection is not available',
                'message': 'Cannot save clipboard content without database connection'
            }), 503  # Service Unavailable
        
        try:
            # Add directly to database
            text_bytes = text.encode('utf-8')
            item_id = db_manager.add_clipboard_item(
                content=text_bytes,
                item_type=ClipItemType.TEXT.value
            )
            return jsonify({'success': True, 'item_id': item_id})
        except Exception as e:
            logger.error(f"Error adding text through database manager: {e}")
            return jsonify({'error': f'Database error: {str(e)}'}), 500
    else:
        # Use clipboard manager as usual
        try:
            item_id = clipboard_manager.add_text_to_clipboard(text)
            
            if item_id:
                return jsonify({'success': True, 'item_id': item_id})
            else:
                return jsonify({'error': 'Failed to add text to clipboard'}), 500
        except Exception as e:
            logger.error(f"Error adding text through clipboard manager: {e}")
            return jsonify({'error': f'Error: {str(e)}'}), 500

@app.route('/api/item/<int:item_id>', methods=['DELETE'])
def delete_item(item_id):
    """Delete a specific clipboard item"""
    result = db_manager.delete_item(item_id)
    
    if result:
        return jsonify({'success': True})
    else:
        return jsonify({'error': 'Failed to delete item'}), 500

@app.route('/api/ping', methods=['GET'])
def ping():
    """Simple endpoint to check if the API is available"""
    # Basic API health check
    api_status = {
        'success': True,
        'api_running': True,
        'message': 'Advanced Clipboard Manager API is running',
        'timestamp': datetime.now().isoformat(),
        'version': '1.0.0'
    }
    
    # Add database connection status
    db_status = False
    db_message = "Database not initialized"
    
    if db_manager is not None:
        try:
            # Try a simple database operation to verify connection
            db_manager.get_recent_items(limit=1)
            db_status = True
            db_message = "Database connection successful"
        except Exception as e:
            db_status = False
            db_message = f"Database error: {str(e)}"
            logger.error(f"Database connection check failed: {e}")
    
    # Add clipboard monitoring status
    if clipboard_manager is not None and hasattr(clipboard_manager, 'monitoring_thread'):
        clipboard_status = clipboard_manager.monitoring_thread is not None and clipboard_manager.monitoring_thread.is_alive()
    else:
        clipboard_status = False
    
    # Environment information
    is_vercel_env = os.environ.get('VERCEL', '') == 'true' or os.environ.get('VERCEL_URL', '')
    
    api_status.update({
        'database_connected': db_status,
        'database_message': db_message,
        'monitoring_active': clipboard_status,
        'environment': 'vercel' if is_vercel_env else 'standard',
        'env_database_url_set': 'DATABASE_URL' in os.environ
    })
    
    return jsonify(api_status)

@app.route('/api/db-status', methods=['GET'])
def db_status():
    """Detailed database status endpoint for diagnostics"""
    # Check if running on Vercel
    is_vercel_env = os.environ.get('VERCEL', '') == 'true' or os.environ.get('VERCEL_URL', '')
    
    status = {
        'success': True,
        'timestamp': datetime.now().isoformat(),
        'database_initialized': db_manager is not None,
        'environment': 'vercel' if is_vercel_env else 'standard',
    }
    
    # Environment variables check (masked for security)
    env_vars = {}
    
    # Check DATABASE_URL
    db_url = os.environ.get('DATABASE_URL')
    if db_url:
        # Mask password
        if '://' in db_url:
            parts = db_url.split('://')
            if '@' in parts[1]:
                auth_part = parts[1].split('@')[0]
                if ':' in auth_part:
                    user = auth_part.split(':')[0]
                    masked_url = f"{parts[0]}://{user}:****@{parts[1].split('@')[1]}"
                    env_vars['DATABASE_URL'] = masked_url
                else:
                    env_vars['DATABASE_URL'] = "Present (no password in URL)"
            else:
                env_vars['DATABASE_URL'] = "Present (no auth in URL)"
        else:
            env_vars['DATABASE_URL'] = "Present (unusual format)"
    else:
        env_vars['DATABASE_URL'] = "Not set"
    
    # Check POSTGRES_ variables
    postgres_vars = ['POSTGRES_USER', 'POSTGRES_HOST', 'POSTGRES_DATABASE', 'POSTGRES_URL_NON_POOLING']
    for var in postgres_vars:
        if var in os.environ:
            if var == 'POSTGRES_USER':
                env_vars[var] = os.environ[var]  # Username is ok to show
            else:
                env_vars[var] = "Present"
        else:
            env_vars[var] = "Not set"
    
    status['environment_variables'] = env_vars
    
    # Database connection test
    if db_manager is not None and hasattr(db_manager, 'engine') and db_manager.engine is not None:
        try:
            engine_info = {
                'dialect': db_manager.engine.name,
                'driver': db_manager.engine.driver,
                'pool_size': db_manager.engine.pool.size(),
            }
            
            # Test basic query
            if hasattr(db_manager, 'Session'):
                session = db_manager.Session()
                try:
                    # Try to execute a simple query
                    result = session.execute(sqlalchemy.text("SELECT 1")).scalar()
                    connection_test = {
                        'success': True,
                        'query_result': result,
                        'message': "Database query successful"
                    }
                    
                    # Get table info
                    table_query = sqlalchemy.text("""
                        SELECT table_name 
                        FROM information_schema.tables 
                        WHERE table_schema='public'
                    """)
                    tables = [row[0] for row in session.execute(table_query)]
                    
                    if 'clipboard_items' in tables:
                        count_query = sqlalchemy.text("SELECT COUNT(*) FROM clipboard_items")
                        item_count = session.execute(count_query).scalar()
                        tables_info = {
                            'tables_found': tables,
                            'clipboard_items_count': item_count
                        }
                    else:
                        tables_info = {
                            'tables_found': tables,
                            'clipboard_items_table': "Not found"
                        }
                    
                    connection_test['tables'] = tables_info
                    
                except Exception as e:
                    connection_test = {
                        'success': False,
                        'error': str(e),
                        'message': "Database query failed"
                    }
                finally:
                    session.close()
            else:
                connection_test = {
                    'success': False,
                    'message': "Session factory not initialized"
                }
            
            status['engine'] = engine_info
            status['connection_test'] = connection_test
            
        except Exception as e:
            status['success'] = False
            status['error'] = str(e)
            status['message'] = "Error checking database status"
    else:
        status['success'] = False
        status['message'] = "Database engine not initialized"
    
    return jsonify(status)

@app.route('/api/system/info', methods=['GET'])
def system_info():
    """Get system information for the browser extension"""
    # Check if running on Vercel
    is_vercel_env = os.environ.get('VERCEL', '') == 'true' or os.environ.get('VERCEL_URL', '')
    
    # Base response with server info
    response = {
        'success': True,
        'server_info': {
            'version': '1.0.0',
            'timestamp': datetime.now().isoformat(),
            'environment': 'vercel' if is_vercel_env else 'standard'
        },
        'stats': {
            'total_items': 0,
            'text_items': 0,
            'image_items': 0,
            'favorite_items': 0,
            'tags_count': 0
        }
    }
    
    # Add clipboard monitoring info if available
    if clipboard_manager is not None:
        if hasattr(clipboard_manager, 'monitoring_thread'):
            response['server_info']['monitoring_active'] = (
                clipboard_manager.monitoring_thread is not None and 
                clipboard_manager.monitoring_thread.is_alive()
            )
        if hasattr(clipboard_manager, 'track_images'):
            response['server_info']['track_images'] = clipboard_manager.track_images
    else:
        response['server_info']['monitoring_active'] = False
        response['server_info']['track_images'] = False
        response['server_info']['clipboard_manager'] = 'unavailable'
    
    # Get database stats if available
    if db_manager is None:
        response['database_status'] = 'unavailable'
        return jsonify(response)
    
    try:
        all_items = db_manager.get_all_items()
        text_items = [item for item in all_items if item.get('type') == ClipItemType.TEXT.value]
        image_items = [item for item in all_items if item.get('type') == ClipItemType.IMAGE.value]
        favorite_items = [item for item in all_items if item.get('favorite')]
        
        # Get unique tags
        all_tags = set()
        for item in all_items:
            if 'tags' in item and item['tags']:
                try:
                    if isinstance(item['tags'], list):
                        all_tags.update(item['tags'])
                    else:
                        tags = json.loads(item['tags'] or '[]')
                        all_tags.update(tags)
                except Exception as e:
                    logger.error(f"Error parsing tags: {e}")
        
        response['stats'] = {
            'total_items': len(all_items),
            'text_items': len(text_items),
            'image_items': len(image_items),
            'favorite_items': len(favorite_items),
            'tags_count': len(all_tags)
        }
        response['database_status'] = 'connected'
        
    except Exception as e:
        logger.error(f"Error retrieving system info: {e}")
        response['database_status'] = 'error'
        response['database_error'] = str(e)
    
    return jsonify(response)

@app.route('/api/extension/copy', methods=['POST'])
def extension_copy():
    """Copy text sent from the browser extension to the clipboard and database"""
    text = request.json.get('text')
    
    if not text:
        return jsonify({'error': 'Text is required'}), 400
    
    # In vercel environment, directly use database manager to add text
    # since clipboard_manager might be None
    if clipboard_manager is None:
        if db_manager is None:
            return jsonify({
                'error': 'Database connection is not available',
                'message': 'Cannot save clipboard content without database connection'
            }), 503  # Service Unavailable
        
        try:
            # Add directly to database
            text_bytes = text.encode('utf-8')
            item_id = db_manager.add_clipboard_item(
                content=text_bytes,
                item_type=ClipItemType.TEXT.value
            )
            return jsonify({'success': True, 'item_id': item_id})
        except Exception as e:
            logger.error(f"Error adding text through database manager: {e}")
            return jsonify({'error': f'Database error: {str(e)}'}), 500
    else:
        # Use clipboard manager as usual
        try:
            item_id = clipboard_manager.add_text_to_clipboard(text)
            
            if item_id:
                return jsonify({'success': True, 'item_id': item_id})
            else:
                return jsonify({'error': 'Failed to add text to clipboard'}), 500
        except Exception as e:
            logger.error(f"Error adding text through clipboard manager: {e}")
            return jsonify({'error': f'Error: {str(e)}'}), 500

def main():
    """Run the web application"""
    # Only start monitoring if not running on Vercel
    if 'VERCEL' not in os.environ:
        # Start the clipboard monitoring service
        clipboard_manager.start_monitoring()
    
    # Run the Flask application
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=False)

if __name__ == "__main__":
    main()