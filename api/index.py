from importlib import import_module
import os
import sys

# Add the root directory to the path so we can import the application
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the vercel setup module
import vercel_setup
vercel_setup.setup_vercel_environment()

# Import the Flask app from web_app.py
from web_app import app

# This module is used for Vercel serverless functions
def handler(request, context):
    """
    This is the entry point for Vercel serverless functions.
    """
    return app(request, context)
