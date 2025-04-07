import os

def setup_vercel_environment():
    """
    Sets up the environment for Vercel deployment.
    Creates necessary database connections and handles environment variables.
    """
    # Check if running on Vercel (several ways to detect)
    is_vercel = os.environ.get('VERCEL', False) or os.environ.get('VERCEL_URL', False)
    
    if is_vercel:
        # Explicitly set VERCEL environment variable for our app to detect
        os.environ['VERCEL'] = 'true'
        
        # Set up database URL from Vercel environment variables
        db_url = os.environ.get('DATABASE_URL')
        
        if not db_url:
            # If DATABASE_URL is not provided, use SQLite as a fallback
            print("No DATABASE_URL found, using SQLite fallback")
            db_url = 'sqlite:///clipboard.db'
        
        # Fix for PostgreSQL URL format if needed
        if db_url and db_url.startswith('postgres://'):
            db_url = db_url.replace('postgres://', 'postgresql://', 1)
            
        os.environ['DATABASE_URL'] = db_url
        
        # Set Flask secret key
        if not os.environ.get('FLASK_SECRET_KEY'):
            os.environ['FLASK_SECRET_KEY'] = os.environ.get('VERCEL_URL', 'default-secret-key')
    
    return True
