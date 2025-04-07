#!/usr/bin/env python3
"""
Web Application Interface for Advanced Clipboard Manager

This module provides a web-based interface to the clipboard manager,
allowing users to access their clipboard history from any browser.
"""
import os
import logging
import json
from datetime import datetime
from flask import Flask, render_template, request, jsonify, redirect, url_for, send_file
from io import BytesIO
import base64

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
db_manager = DatabaseManager()
clipboard_manager = ClipboardManager(db_manager)

@app.route('/')
def index():
    """Render the main page"""
    return render_template('index.html')

@app.route('/api/items')
def get_items():
    """Get clipboard items with optional filtering"""
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
            'tags': json.loads(item.get('tags') or '[]')
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

@app.route('/api/item/<int:item_id>')
def get_item(item_id):
    """Get a specific clipboard item"""
    item = db_manager.get_item_by_id(item_id)
    
    if not item:
        return jsonify({'error': 'Item not found'}), 404
        
    processed_item = {
        'id': item.get('id'),
        'type': item.get('type'),
        'timestamp': format_timestamp(item.get('timestamp')),
        'favorite': item.get('favorite', False),
        'tags': json.loads(item.get('tags') or '[]')
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
        tags = json.loads(item.get('tags') or '[]')
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

def main():
    """Run the web application"""
    # Start the clipboard monitoring service
    clipboard_manager.start_monitoring()
    
    # Run the Flask application
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=False)

if __name__ == "__main__":
    main()