from flask import Flask, jsonify, request
from flask_cors import CORS
import json
import os
from datetime import datetime

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Path to the JSON file - Vercel serverless environment
def get_json_path():
    """Get the correct path to all_articles.json"""
    # Try multiple paths for Vercel serverless
    possible_paths = [
        os.path.join(os.path.dirname(__file__), '..', 'all_articles.json'),
        os.path.join(os.getcwd(), 'all_articles.json'),
        '/var/task/all_articles.json',
        'all_articles.json'
    ]
    
    for path in possible_paths:
        if os.path.exists(path):
            return path
    
    # Return first path as fallback
    return possible_paths[0]

JSON_FILE_PATH = get_json_path()

def load_articles():
    """Load articles from JSON file"""
    try:
        with open(JSON_FILE_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        return {
            "sources": [],
            "scraped_at": None,
            "total_articles": 0,
            "articles": []
        }
    except json.JSONDecodeError:
        return {
            "sources": [],
            "scraped_at": None,
            "total_articles": 0,
            "articles": []
        }

@app.route('/')
def home():
    """API documentation endpoint"""
    return jsonify({
        "name": "Tech News Scraper API",
        "version": "1.0.0",
        "description": "REST API for accessing scraped tech news articles from The Verge, TechCrunch, and CNET",
        "endpoints": {
            "GET /": "API documentation",
            "GET /api/articles": "Get all articles",
            "GET /api/articles?source=<source>": "Filter by source (The Verge, TechCrunch, CNET)",
            "GET /api/articles?category=<category>": "Filter by category (Trending, Technology, Education, Careers, AI & ML)",
            "GET /api/articles?limit=<number>": "Limit number of results",
            "GET /api/articles?page=<number>&per_page=<number>": "Paginate results",
            "GET /api/sources": "Get list of all sources",
            "GET /api/categories": "Get list of all categories",
            "GET /api/stats": "Get statistics about scraped articles"
        }
    })

@app.route('/api/articles', methods=['GET'])
def get_articles():
    """Get articles with optional filtering and pagination"""
    data = load_articles()
    articles = data.get('articles', [])
    
    # Filter by source
    source = request.args.get('source')
    if source:
        articles = [a for a in articles if a.get('source', '').lower() == source.lower()]
    
    # Filter by category
    category = request.args.get('category')
    if category:
        articles = [a for a in articles if a.get('category', '').lower() == category.lower()]
    
    # Search by keyword in title or description
    search = request.args.get('search')
    if search:
        search_lower = search.lower()
        articles = [a for a in articles if 
                   search_lower in a.get('title', '').lower() or 
                   search_lower in a.get('description', '').lower()]
    
    # Filter by date
    date_from = request.args.get('date_from')
    date_to = request.args.get('date_to')
    if date_from or date_to:
        filtered = []
        for a in articles:
            if a.get('published_date'):
                try:
                    article_date = datetime.fromisoformat(a['published_date'].replace('Z', '+00:00'))
                    if date_from and article_date < datetime.fromisoformat(date_from):
                        continue
                    if date_to and article_date > datetime.fromisoformat(date_to):
                        continue
                    filtered.append(a)
                except:
                    continue
        articles = filtered
    
    # Pagination
    page = request.args.get('page', type=int)
    per_page = request.args.get('per_page', type=int, default=10)
    limit = request.args.get('limit', type=int)
    
    total_articles = len(articles)
    
    if page and per_page:
        start = (page - 1) * per_page
        end = start + per_page
        articles = articles[start:end]
        
        return jsonify({
            "success": True,
            "data": {
                "articles": articles,
                "pagination": {
                    "page": page,
                    "per_page": per_page,
                    "total": total_articles,
                    "total_pages": (total_articles + per_page - 1) // per_page
                }
            },
            "scraped_at": data.get('scraped_at')
        })
    elif limit:
        articles = articles[:limit]
    
    return jsonify({
        "success": True,
        "data": {
            "articles": articles,
            "total": total_articles
        },
        "scraped_at": data.get('scraped_at')
    })

@app.route('/api/sources', methods=['GET'])
def get_sources():
    """Get list of all available sources"""
    data = load_articles()
    return jsonify({
        "success": True,
        "data": {
            "sources": data.get('sources', [])
        }
    })

@app.route('/api/categories', methods=['GET'])
def get_categories():
    """Get list of all categories"""
    data = load_articles()
    articles = data.get('articles', [])
    categories = list(set([a.get('category') for a in articles if a.get('category')]))
    
    return jsonify({
        "success": True,
        "data": {
            "categories": sorted(categories)
        }
    })

@app.route('/api/stats', methods=['GET'])
def get_stats():
    """Get statistics about scraped articles"""
    data = load_articles()
    articles = data.get('articles', [])
    
    # Count by source
    source_counts = {}
    for article in articles:
        source = article.get('source', 'Unknown')
        source_counts[source] = source_counts.get(source, 0) + 1
    
    # Count by category
    category_counts = {}
    for article in articles:
        category = article.get('category', 'Unknown')
        category_counts[category] = category_counts.get(category, 0) + 1
    
    return jsonify({
        "success": True,
        "data": {
            "total_articles": data.get('total_articles', 0),
            "sources": data.get('sources', []),
            "scraped_at": data.get('scraped_at'),
            "articles_by_source": source_counts,
            "articles_by_category": category_counts
        }
    })

@app.errorhandler(404)
def not_found(error):
    return jsonify({
        "success": False,
        "error": "Endpoint not found"
    }), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({
        "success": False,
        "error": "Internal server error"
    }), 500

