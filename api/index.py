# Vercel serverless entrypoint
import os
import sys

# Add parent directory to path to import app
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

# Set Vercel deployment flag
os.environ['VERCEL_DEPLOYMENT'] = 'true'

# Import the Flask app (disables SocketIO/APScheduler when VERCEL_DEPLOYMENT is set)
from app import app

# Vercel expects an 'app' variable
# This is the WSGI application that Vercel will call
app = app
