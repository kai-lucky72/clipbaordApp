from importlib import import_module
import os
import sys
import logging

# Add the root directory to the path so we can import the application
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Basic logging setup first
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger('vercel_handler')

# Import the vercel setup module
try:
    logger.info("Setting up Vercel environment...")
    import vercel_setup
    vercel_setup.setup_vercel_environment()
    logger.info("Vercel environment setup complete")
    
    # Import utils for logging setup
    from utils import setup_logger
    setup_logger()  # Configure proper logging
    
    # Import SQLAlchemy to check if it's properly installed
    try:
        import sqlalchemy
        logger.info(f"SQLAlchemy version: {sqlalchemy.__version__}")
    except ImportError:
        logger.error("SQLAlchemy is not installed or cannot be imported")
    
    # Verify DATABASE_URL
    db_url = os.environ.get('DATABASE_URL')
    if db_url:
        # Mask password for security
        if '://' in db_url:
            parts = db_url.split('://')
            if '@' in parts[1]:
                auth_part = parts[1].split('@')[0]
                if ':' in auth_part:
                    user = auth_part.split(':')[0]
                    masked_url = f"{parts[0]}://{user}:****@{parts[1].split('@')[1]}"
                    logger.info(f"DATABASE_URL format: {masked_url}")
                else:
                    logger.info(f"DATABASE_URL provided (no password in URL)")
            else:
                logger.info(f"DATABASE_URL provided (no auth in URL)")
        else:
            logger.info(f"DATABASE_URL provided (unusual format)")
    else:
        logger.warning("No DATABASE_URL found in environment")
    
    # Verify Flask secret key
    if os.environ.get('FLASK_SECRET_KEY'):
        logger.info("FLASK_SECRET_KEY is set")
    else:
        logger.warning("FLASK_SECRET_KEY is not set")
    
    # Import the Flask app from web_app.py
    logger.info("Importing Flask app from web_app.py...")
    from web_app import app
    logger.info("Flask app imported successfully")
    
except Exception as e:
    logger.error(f"Error in Vercel setup: {str(e)}", exc_info=True)
    # In case of critical error, create a minimal Flask app to return error info
    from flask import Flask, jsonify
    app = Flask(__name__)
    
    @app.route('/api/db-status')
    def db_status():
        """Special database debug endpoint for Vercel deployment"""
        import json
        import os
        
        # Environment information
        is_vercel = os.environ.get('VERCEL', '') == 'true' or os.environ.get('VERCEL_URL', '')
        
        status = {
            'success': False,
            'message': 'Database connection error during initialization',
            'error': str(e),
            'timestamp': __import__('datetime').datetime.now().isoformat(),
            'environment': 'vercel' if is_vercel else 'standard',
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
        
        # Check other environment variables
        postgres_vars = ['POSTGRES_USER', 'POSTGRES_HOST', 'POSTGRES_DATABASE', 'POSTGRES_PASSWORD', 'POSTGRES_URL_NON_POOLING']
        for var in postgres_vars:
            if var in os.environ:
                if var == 'POSTGRES_USER':
                    env_vars[var] = os.environ[var]  # Username is ok to show
                else:
                    env_vars[var] = "Present"
            else:
                env_vars[var] = "Not set"
        
        # Package versions
        packages = {
            'sqlalchemy': 'Not installed',
            'flask': 'Not installed',
            'psycopg2': 'Not installed'
        }
        
        try:
            import sqlalchemy
            packages['sqlalchemy'] = sqlalchemy.__version__
        except:
            pass
            
        try:
            import flask
            packages['flask'] = flask.__version__
        except:
            pass
            
        try:
            import psycopg2
            packages['psycopg2'] = psycopg2.__version__
        except:
            pass
        
        status['environment_variables'] = env_vars
        status['packages'] = packages
        
        return jsonify(status)
    
    @app.route('/', defaults={'path': ''})
    @app.route('/<path:path>')
    def catch_all(path):
        return jsonify({
            'error': 'Initialization Error',
            'message': str(e),
            'setup_stage': 'Vercel environment setup',
            'timestamp': __import__('datetime').datetime.now().isoformat()
        }), 500

# This module is used for Vercel serverless functions
def handler(request, context):
    """
    This is the entry point for Vercel serverless functions.
    """
    try:
        return app(request, context)
    except Exception as e:
        logger.error(f"Error handling request: {str(e)}", exc_info=True)
        
        # Return a detailed JSON error response
        from flask import jsonify
        import os
        import sys
        import traceback
        
        # Full traceback for debugging
        exc_type, exc_value, exc_traceback = sys.exc_info()
        tb_lines = traceback.format_exception(exc_type, exc_value, exc_traceback)
        
        # Environment information
        is_vercel = os.environ.get('VERCEL', '') == 'true' or os.environ.get('VERCEL_URL', '')
        
        # Check DATABASE_URL (masked for security)
        db_url_status = "Not set"
        db_url = os.environ.get('DATABASE_URL')
        if db_url:
            if '://' in db_url:
                parts = db_url.split('://')
                if '@' in parts[1]:
                    auth_part = parts[1].split('@')[0]
                    if ':' in auth_part:
                        db_url_status = f"{parts[0]}://{auth_part.split(':')[0]}:****@{parts[1].split('@')[1]}"
                    else:
                        db_url_status = "Present (no password in URL)"
                else:
                    db_url_status = "Present (no auth in URL)"
            else:
                db_url_status = "Present (unusual format)"
        
        # Prepare a comprehensive error response
        response = jsonify({
            'error': 'Server Error',
            'message': str(e),
            'error_type': exc_type.__name__ if exc_type else "Unknown",
            'traceback': tb_lines,
            'timestamp': __import__('datetime').datetime.now().isoformat(),
            'environment': {
                'is_vercel': is_vercel,
                'database_url': db_url_status,
                'python_version': sys.version,
                'env_variables': list(os.environ.keys())  # Just list names, not values for security
            },
            'request_info': {
                'path': request.get('path', 'Unknown'),
                'method': request.get('method', 'Unknown'),
                'query': request.get('query', {})
            }
        })
        response.status_code = 500
        return response
