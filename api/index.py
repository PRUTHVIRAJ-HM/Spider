from app import app

# Export the Flask app for Vercel
# Vercel's @vercel/python builder will automatically handle the Flask app
handler = app

