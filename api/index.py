import sys
import os

# Ensure we can import from the api directory
sys.path.insert(0, os.path.dirname(__file__))

from app import app

# Export for Vercel serverless functions
handler = app

