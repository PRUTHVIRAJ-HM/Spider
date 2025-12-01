import requests
import json

print("=" * 60)
print("Testing Tech News Scraper API")
print("=" * 60)

base_url = "http://localhost:5000"

# Test 1: API Documentation
print("\n1. Testing GET / (API Documentation)")
try:
    response = requests.get(f"{base_url}/")
    print(f"Status: {response.status_code}")
    print(json.dumps(response.json(), indent=2))
except Exception as e:
    print(f"Error: {e}")

# Test 2: Get Statistics
print("\n2. Testing GET /api/stats")
try:
    response = requests.get(f"{base_url}/api/stats")
    print(f"Status: {response.status_code}")
    data = response.json()
    print(json.dumps(data, indent=2))
except Exception as e:
    print(f"Error: {e}")

# Test 3: Get Sources
print("\n3. Testing GET /api/sources")
try:
    response = requests.get(f"{base_url}/api/sources")
    print(f"Status: {response.status_code}")
    print(json.dumps(response.json(), indent=2))
except Exception as e:
    print(f"Error: {e}")

# Test 4: Get Categories
print("\n4. Testing GET /api/categories")
try:
    response = requests.get(f"{base_url}/api/categories")
    print(f"Status: {response.status_code}")
    print(json.dumps(response.json(), indent=2))
except Exception as e:
    print(f"Error: {e}")

# Test 5: Get Articles with limit
print("\n5. Testing GET /api/articles?limit=3")
try:
    response = requests.get(f"{base_url}/api/articles?limit=3")
    print(f"Status: {response.status_code}")
    data = response.json()
    print(f"Total articles: {data['data']['total']}")
    print(f"Returned: {len(data['data']['articles'])}")
    for i, article in enumerate(data['data']['articles'], 1):
        print(f"\n  Article {i}:")
        print(f"    Title: {article.get('title', 'N/A')[:60]}...")
        print(f"    Source: {article.get('source', 'N/A')}")
        print(f"    Category: {article.get('category', 'N/A')}")
except Exception as e:
    print(f"Error: {e}")

# Test 6: Filter by source
print("\n6. Testing GET /api/articles?source=CNET&limit=2")
try:
    response = requests.get(f"{base_url}/api/articles?source=CNET&limit=2")
    print(f"Status: {response.status_code}")
    data = response.json()
    print(f"Total CNET articles: {data['data']['total']}")
    for i, article in enumerate(data['data']['articles'], 1):
        print(f"\n  Article {i}:")
        print(f"    Title: {article.get('title', 'N/A')[:60]}...")
        print(f"    Source: {article.get('source', 'N/A')}")
except Exception as e:
    print(f"Error: {e}")

# Test 7: Filter by category
print("\n7. Testing GET /api/articles?category=Technology&limit=2")
try:
    response = requests.get(f"{base_url}/api/articles?category=Technology&limit=2")
    print(f"Status: {response.status_code}")
    data = response.json()
    print(f"Total Technology articles: {data['data']['total']}")
    for i, article in enumerate(data['data']['articles'], 1):
        print(f"\n  Article {i}:")
        print(f"    Title: {article.get('title', 'N/A')[:60]}...")
        print(f"    Category: {article.get('category', 'N/A')}")
except Exception as e:
    print(f"Error: {e}")

# Test 8: Search
print("\n8. Testing GET /api/articles?search=AI&limit=2")
try:
    response = requests.get(f"{base_url}/api/articles?search=AI&limit=2")
    print(f"Status: {response.status_code}")
    data = response.json()
    print(f"Total articles with 'AI': {data['data']['total']}")
    for i, article in enumerate(data['data']['articles'], 1):
        print(f"\n  Article {i}:")
        print(f"    Title: {article.get('title', 'N/A')[:60]}...")
except Exception as e:
    print(f"Error: {e}")

# Test 9: Pagination
print("\n9. Testing GET /api/articles?page=1&per_page=5")
try:
    response = requests.get(f"{base_url}/api/articles?page=1&per_page=5")
    print(f"Status: {response.status_code}")
    data = response.json()
    print(f"Page: {data['data']['pagination']['page']}")
    print(f"Per page: {data['data']['pagination']['per_page']}")
    print(f"Total: {data['data']['pagination']['total']}")
    print(f"Total pages: {data['data']['pagination']['total_pages']}")
    print(f"Returned articles: {len(data['data']['articles'])}")
except Exception as e:
    print(f"Error: {e}")

print("\n" + "=" * 60)
print("All tests completed!")
print("=" * 60)
