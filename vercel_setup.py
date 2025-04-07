import os
import sys
import logging
import platform
import json

# Set up basic logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger('vercel_setup')

def setup_vercel_environment():
    """
    Sets up the environment for Vercel deployment.
    Creates necessary database connections and handles environment variables.
    """
    # Environment diagnostic info
    logger.info(f"Python version: {sys.version}")
    logger.info(f"Platform: {platform.platform()}")
    
    # Check if running on Vercel (several ways to detect)
    is_vercel = os.environ.get('VERCEL', False) or os.environ.get('VERCEL_URL', False)
    logger.info(f"Running on Vercel: {bool(is_vercel)}")
    
    # Log available environment variables (without sensitive values)
    env_var_names = sorted(os.environ.keys())
    logger.info(f"Available environment variables: {', '.join(env_var_names)}")
    
    if is_vercel:
        # Explicitly set VERCEL environment variable for our app to detect
        os.environ['VERCEL'] = 'true'
        logger.info("Set VERCEL=true in environment")
        
        # Set up database URL from Vercel environment variables
        db_url = os.environ.get('DATABASE_URL')
        
        if not db_url:
            logger.info("No DATABASE_URL found, trying to construct one")
            
            # Try to construct DATABASE_URL from Supabase environment variables
            pg_user = os.environ.get('POSTGRES_USER')
            pg_password = os.environ.get('POSTGRES_PASSWORD')
            pg_host = os.environ.get('POSTGRES_HOST')
            pg_database = os.environ.get('POSTGRES_DATABASE')
            
            # Log available PostgreSQL variables (without showing passwords)
            pg_vars = {
                'POSTGRES_USER': pg_user or 'Not set',
                'POSTGRES_HOST': pg_host or 'Not set',
                'POSTGRES_DATABASE': pg_database or 'Not set',
                'POSTGRES_PASSWORD': 'Present' if pg_password else 'Not set'
            }
            logger.info(f"PostgreSQL variables: {json.dumps(pg_vars)}")
            
            if pg_user and pg_password and pg_host and pg_database:
                # Construct a proper DATABASE_URL for SQLAlchemy
                db_url = f"postgresql://{pg_user}:{pg_password}@{pg_host}/{pg_database}"
                logger.info(f"Constructed DATABASE_URL from Supabase credentials")
                
                # Test connection format
                connection_parts = []
                if '://' in db_url:
                    connection_parts.append("Has protocol")
                if '@' in db_url:
                    connection_parts.append("Has credentials")
                if '/' in db_url.split('@')[-1]:
                    connection_parts.append("Has database name")
                logger.info(f"Connection URL format checks: {', '.join(connection_parts)}")
            else:
                # If no Supabase credentials, check for URL_NON_POOLING
                db_url = os.environ.get('POSTGRES_URL_NON_POOLING')
                if db_url:
                    logger.info(f"Using POSTGRES_URL_NON_POOLING for database connection")
                else:
                    # Last resort fallback - note we want to avoid SQLite in Vercel
                    logger.warning("No PostgreSQL credentials found, using SQLite fallback (this is not recommended in Vercel)")
                    db_url = 'sqlite:///clipboard.db'
        else:
            logger.info("Found existing DATABASE_URL in environment")
            
            # Test connection format
            connection_parts = []
            if '://' in db_url:
                connection_parts.append("Has protocol")
                
                # Check protocol type
                protocol = db_url.split('://')[0]
                connection_parts.append(f"Protocol: {protocol}")
                
                if protocol == 'postgres':
                    logger.info("Detected 'postgres://' prefix, will convert to 'postgresql://'")
            
            if '@' in db_url:
                connection_parts.append("Has credentials")
            if '/' in db_url.split('@')[-1]:
                connection_parts.append("Has database name")
                
            logger.info(f"Connection URL format checks: {', '.join(connection_parts)}")
        
        # Fix for PostgreSQL URL format if needed
        if db_url and db_url.startswith('postgres://'):
            original_url = db_url
            db_url = db_url.replace('postgres://', 'postgresql://', 1)
            logger.info(f"Fixed DATABASE_URL format: 'postgres://' -> 'postgresql://'")
        
        # Log masked version of database URL for debugging
        if db_url:
            masked_url = None
            if '://' in db_url:
                parts = db_url.split('://')
                if '@' in parts[1]:
                    auth_part = parts[1].split('@')[0]
                    if ':' in auth_part:
                        user = auth_part.split(':')[0]
                        masked_url = f"{parts[0]}://{user}:****@{parts[1].split('@')[1]}"
                    else:
                        masked_url = f"{parts[0]}://{auth_part}@{parts[1].split('@')[1]}"
                else:
                    masked_url = db_url
            else:
                masked_url = db_url
            
            logger.info(f"Using database URL: {masked_url}")
            
        os.environ['DATABASE_URL'] = db_url
        logger.info(f"DATABASE_URL set in environment")
        
        # Set Flask secret key
        if not os.environ.get('FLASK_SECRET_KEY'):
            # Use SUPABASE_JWT_SECRET if available, otherwise fallback
            flask_secret_source = 'SUPABASE_JWT_SECRET' if os.environ.get('SUPABASE_JWT_SECRET') else 'VERCEL_URL'
            flask_secret = os.environ.get('SUPABASE_JWT_SECRET') or os.environ.get('VERCEL_URL', 'default-secret-key')
            os.environ['FLASK_SECRET_KEY'] = flask_secret
            logger.info(f"Flask secret key configured using {flask_secret_source}")
        else:
            logger.info("Using existing FLASK_SECRET_KEY")
        
        # Verify imports that will be needed
        try:
            import sqlalchemy
            logger.info(f"SQLAlchemy import successful, version: {sqlalchemy.__version__}")
        except ImportError as e:
            logger.error(f"Failed to import SQLAlchemy: {str(e)}")
            logger.info("Trying to see if sqlalchemy is even installed...")
            if 'sqlalchemy' in sys.modules:
                logger.info("SQLAlchemy found in sys.modules but import failed")
            
            try:
                import pkg_resources
                logger.info(f"Installed packages: {[d.project_name for d in pkg_resources.working_set]}")
            except:
                logger.error("Failed to list installed packages")
        
        try:
            import flask
            logger.info(f"Flask import successful, version: {flask.__version__}")
        except ImportError as e:
            logger.error(f"Failed to import Flask: {str(e)}")
        
        try:
            import psycopg2
            logger.info(f"psycopg2 import successful, version: {psycopg2.__version__ if hasattr(psycopg2, '__version__') else 'unknown'}")
        except ImportError as e:
            logger.error(f"Failed to import psycopg2: {str(e)}")
    
    else:
        logger.info("Not running on Vercel, skipping Vercel-specific setup")
    
    logger.info("Environment setup complete")
    return True
