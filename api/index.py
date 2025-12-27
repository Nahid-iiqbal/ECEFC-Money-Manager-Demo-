# Vercel serverless entrypoint
import os
import sys
import traceback

# Add parent directory to path to import app
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

# Set Vercel deployment flag
os.environ['VERCEL_DEPLOYMENT'] = 'true'

# Import the Flask app (disables SocketIO/APScheduler when VERCEL_DEPLOYMENT is set)
try:
    from app import app
    print("Flask app imported successfully")
    
    # Verify critical environment variables
    if not os.environ.get('SECRET_KEY'):
        print("WARNING: SECRET_KEY not set - using default (not secure!)")
    
    if not os.environ.get('DATABASE_URL'):
        print("WARNING: DATABASE_URL not set - using SQLite (not persistent on Vercel!)")
    else:
        print(f"DATABASE_URL configured: {os.environ.get('DATABASE_URL')[:30]}...")
    
    # Vercel expects an 'app' variable
    # This is the WSGI application that Vercel will call
    app = app
    
except Exception as e:
    print(f"CRITICAL ERROR: Failed to import Flask app")
    print(f"Error: {str(e)}")
    print(f"Traceback:\n{traceback.format_exc()}")
    raise
