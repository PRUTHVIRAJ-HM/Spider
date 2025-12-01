import os
from dotenv import load_dotenv
import requests
import time

# Load environment variables
load_dotenv()

PIXABAY_API_KEY = os.getenv('PIXABAY_API_KEY')
UNSPLASH_ACCESS_KEY = os.getenv('UNSPLASH_ACCESS_KEY')

def get_thumbnail_from_pixabay(query):
    """Fetch thumbnail from Pixabay API"""
    if not PIXABAY_API_KEY:
        return None
    
    try:
        url = "https://pixabay.com/api/"
        params = {
            'key': PIXABAY_API_KEY,
            'q': query,
            'image_type': 'photo',
            'per_page': 3,
            'safesearch': 'true',
            'orientation': 'horizontal'
        }
        
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if data.get('hits') and len(data['hits']) > 0:
            # Return the first image's webformat URL (optimized for web)
            return data['hits'][0]['webformatURL']
        
        return None
    except Exception as e:
        print(f"      Error fetching from Pixabay: {e}")
        return None

def get_thumbnail_from_unsplash(query):
    """Fetch thumbnail from Unsplash API"""
    if not UNSPLASH_ACCESS_KEY:
        return None
    
    try:
        url = "https://api.unsplash.com/search/photos"
        headers = {
            'Authorization': f'Client-ID {UNSPLASH_ACCESS_KEY}'
        }
        params = {
            'query': query,
            'per_page': 1,
            'orientation': 'landscape'
        }
        
        response = requests.get(url, headers=headers, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if data.get('results') and len(data['results']) > 0:
            # Return the regular sized image URL
            return data['results'][0]['urls']['regular']
        
        return None
    except Exception as e:
        print(f"      Error fetching from Unsplash: {e}")
        return None

def extract_keywords_from_title(title):
    """Extract meaningful keywords from article title"""
    if not title:
        return []
    
    # Common words to exclude
    stop_words = {
        'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 
        'of', 'with', 'by', 'from', 'up', 'about', 'into', 'through', 'during',
        'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had',
        'do', 'does', 'did', 'will', 'would', 'should', 'could', 'may', 'might',
        'can', 'this', 'that', 'these', 'those', 'i', 'you', 'he', 'she', 'it',
        'we', 'they', 'what', 'which', 'who', 'when', 'where', 'why', 'how',
        'all', 'each', 'every', 'both', 'few', 'more', 'most', 'other', 'some',
        'such', 'no', 'nor', 'not', 'only', 'own', 'same', 'so', 'than', 'too',
        'very', 's', 't', 'just', 'now', 'get', 'got', 'here', 'there'
    }
    
    # Remove special characters and split
    import re
    words = re.findall(r'\b[a-zA-Z]+\b', title.lower())
    
    # Filter out stop words and short words
    keywords = [w for w in words if w not in stop_words and len(w) > 3]
    
    # Return first 4 meaningful words
    return keywords[:4]

def get_article_thumbnail(title, category=None):
    """
    Get thumbnail for an article from Pixabay or Unsplash
    Uses title to search for relevant images
    Falls back to category if title search fails
    """
    if not title:
        return None
    
    # Extract keywords from title
    keywords = extract_keywords_from_title(title)
    
    if not keywords:
        # If no keywords extracted, use first 50 chars of title
        search_query = title[:50].strip()
    else:
        # Join keywords for search
        search_query = ' '.join(keywords)
    
    print(f"      Searching images for: {search_query}")
    
    # Try Pixabay first
    thumbnail = get_thumbnail_from_pixabay(search_query)
    
    # If Pixabay fails, try Unsplash
    if not thumbnail:
        time.sleep(0.5)  # Small delay between API calls
        thumbnail = get_thumbnail_from_unsplash(search_query)
    
    # If both fail and we have a category, try category as fallback
    if not thumbnail and category and category != 'Unknown':
        print(f"      Trying category fallback: {category}")
        thumbnail = get_thumbnail_from_pixabay(category)
        if not thumbnail:
            time.sleep(0.5)
            thumbnail = get_thumbnail_from_unsplash(category)
    
    return thumbnail
