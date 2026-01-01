import requests
from bs4 import BeautifulSoup
import json
import ollama
from datetime import datetime
from typing import List, Dict
import os
from dotenv import load_dotenv
from image_fetcher import get_article_thumbnail

load_dotenv()


class NewsScraperWithAI:
    """Web scraper for tech news sites that uses Ollama to structure data."""
    
    def __init__(self, base_url: str = "https://www.theverge.com/", source_name: str = "The Verge", ollama_model: str = None):
        self.base_url = base_url
        self.source_name = source_name
        # Get model from parameter, environment variable, or use default
        self.ollama_model = ollama_model or os.getenv('OLLAMA_MODEL', 'llama3.2:3b')
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
    
    def fetch_page(self) -> BeautifulSoup:
        """Fetch the main page."""
        print(f"Fetching content from {self.base_url}...")
        response = requests.get(self.base_url, headers=self.headers)
        response.raise_for_status()
        return BeautifulSoup(response.content, 'lxml')
    
    def extract_articles_verge(self, soup: BeautifulSoup) -> List[Dict]:
        """Extract article information from The Verge."""
        articles = []
        seen_urls = set()
        
        # Find all time elements - The Verge uses these extensively for article timestamps
        time_elements = soup.find_all('time')
        print(f"Found {len(time_elements)} time elements")
        
        # For each time element, find the associated article
        for time_elem in time_elements:
            # Go up the DOM tree to find the article container
            container = time_elem.parent
            
            for _ in range(6):  # Search up to 6 levels
                if not container:
                    break
                
                # Look for a link in this container
                link = container.find('a', href=lambda x: x and x.startswith('/'))
                
                if link:
                    url = link.get('href')
                    
                    # Skip if already processed
                    if url in seen_urls:
                        break
                    
                    # Make absolute URL
                    if url.startswith('/'):
                        full_url = 'https://www.theverge.com' + url
                    else:
                        full_url = url
                    
                    # Extract article data
                    article_data = {
                        'url': full_url,
                        'title': link.get_text(strip=True),
                        'published_date': time_elem.get('datetime', time_elem.get_text(strip=True))
                    }
                    
                    # Try to find description/excerpt in the container
                    # Look for paragraph elements that might be descriptions
                    description_found = False
                    for p in container.find_all('p', limit=10):
                        text = p.get_text(strip=True)
                        # Check if it's a substantial description (not just a link or short text)
                        if len(text) > 30 and text != article_data['title'] and not description_found:
                            # Avoid using overly long paragraphs that are likely full articles
                            if len(text) < 500:
                                article_data['description'] = text
                                description_found = True
                                break
                    
                    # If no description found, try parent containers
                    if not description_found and container.parent:
                        for p in container.parent.find_all('p', limit=5):
                            text = p.get_text(strip=True)
                            if len(text) > 30 and len(text) < 500 and text != article_data['title']:
                                article_data['description'] = text
                                break
                    
                    # Try to find author
                    # Look for common author patterns
                    author_elem = container.find('a', class_=lambda x: x and 'author' in str(x).lower())
                    if not author_elem:
                        # Alternative: look for spans with "by" text
                        author_elem = container.find('span', string=lambda x: x and 'by' in str(x).lower() if x else False)
                    
                    if author_elem:
                        article_data['author'] = author_elem.get_text(strip=True).replace('By ', '').replace('by ', '')
                    
                    # Add to list and mark as seen
                    seen_urls.add(url)
                    articles.append(article_data)
                    break
                
                # Move up to parent
                container = container.parent
            
            # Limit to avoid processing too many articles
            if len(articles) >= 20:
                break
        
        print(f"Extracted {len(articles)} unique articles")
        return articles
    
    def extract_articles_techcrunch(self, soup: BeautifulSoup) -> List[Dict]:
        """Extract article information from TechCrunch."""
        articles = []
        seen_urls = set()
        
        # TechCrunch uses article tags with specific classes
        article_elements = soup.find_all('article', class_=lambda x: x and 'post-block' in str(x))
        
        # Also try finding by div with post classes
        if not article_elements:
            article_elements = soup.find_all(['article', 'div'], class_=lambda x: x and 'post' in str(x))
        
        print(f"Found {len(article_elements)} article elements")
        
        for article_elem in article_elements[:20]:
            # Find title - usually in h2 or h3 with a link
            title_elem = article_elem.find(['h2', 'h3', 'h1'])
            if not title_elem:
                continue
            
            # Find link
            link = title_elem.find('a') or article_elem.find('a', href=True)
            if not link:
                continue
            
            url = link.get('href', '')
            if not url or url in seen_urls:
                continue
            
            # Make absolute URL if needed
            if url.startswith('/'):
                url = 'https://techcrunch.com' + url
            
            seen_urls.add(url)
            
            article_data = {
                'url': url,
                'title': title_elem.get_text(strip=True),
                'source': 'TechCrunch'
            }
            
            # Find description/excerpt - check multiple strategies
            desc_elem = article_elem.find('p', class_=lambda x: x and ('excerpt' in str(x) or 'summary' in str(x) or 'subtitle' in str(x)))
            
            if not desc_elem:
                # Try to find first substantial paragraph
                for p in article_elem.find_all('p', limit=5):
                    desc_text = p.get_text(strip=True)
                    if len(desc_text) > 30 and len(desc_text) < 500:
                        article_data['description'] = desc_text
                        desc_elem = True  # Mark as found
                        break
            elif desc_elem:
                desc_text = desc_elem.get_text(strip=True)
                if len(desc_text) > 30 and len(desc_text) < 500:
                    article_data['description'] = desc_text
            
            # Find author
            author_elem = article_elem.find('a', class_=lambda x: x and 'author' in str(x))
            if not author_elem:
                author_elem = article_elem.find('span', class_=lambda x: x and 'author' in str(x))
            if author_elem:
                article_data['author'] = author_elem.get_text(strip=True)
            
            # Find date
            time_elem = article_elem.find('time')
            if time_elem:
                article_data['published_date'] = time_elem.get('datetime', time_elem.get_text(strip=True))
            
            articles.append(article_data)
        
        print(f"Extracted {len(articles)} unique articles")
        return articles
    
    def extract_articles_cnet(self, soup: BeautifulSoup) -> List[Dict]:
        """Extract article information from CNET."""
        articles = []
        seen_urls = set()
        
        # CNET uses H3 elements for article titles
        h3_elements = soup.find_all('h3')
        print(f"Found {len(h3_elements)} H3 elements")
        
        for h3 in h3_elements[:20]:
            # Find link in or around H3
            link = h3.find('a') or h3.find_parent('a')
            if not link:
                continue
            
            url = link.get('href', '')
            if not url or url in seen_urls:
                continue
            
            # Make absolute URL if needed
            if url.startswith('/'):
                url = 'https://www.cnet.com' + url
            
            # Skip non-article URLs (navigation, etc.)
            if not any(x in url for x in ['/tech/', '/deals/', '/news/', '/reviews/', '/how-to/']):
                continue
            
            seen_urls.add(url)
            
            article_data = {
                'url': url,
                'title': h3.get_text(strip=True),
                'source': 'CNET'
            }
            
            # Find description in parent container or article wrapper
            container = h3.parent
            description_found = False
            
            for _ in range(7):
                if not container or description_found:
                    break
                
                # Search for all paragraphs in this container
                for p in container.find_all('p', limit=5):
                    desc_text = p.get_text(strip=True)
                    # Look for substantial descriptions, avoiding titles and short text
                    if len(desc_text) > 30 and len(desc_text) < 600 and desc_text != article_data['title']:
                        article_data['description'] = desc_text
                        description_found = True
                        break
                
                container = container.parent
            
            articles.append(article_data)
        
        print(f"Extracted {len(articles)} unique articles")
        return articles
    
    def extract_articles(self, soup: BeautifulSoup) -> List[Dict]:
        """Route to appropriate extraction method based on source."""
        if 'techcrunch' in self.base_url.lower():
            return self.extract_articles_techcrunch(soup)
        elif 'cnet' in self.base_url.lower():
            return self.extract_articles_cnet(soup)
        else:
            return self.extract_articles_verge(soup)
    
    def structure_with_ollama(self, articles: List[Dict]) -> List[Dict]:
        """Use Ollama to structure and clean the article data."""
        print(f"\nProcessing {len(articles)} articles with Ollama ({self.ollama_model})...")
        
        structured_articles = []
        
        for idx, article in enumerate(articles, 1):
            print(f"Processing article {idx}/{len(articles)}: {article.get('title', 'Untitled')[:50]}...")
            
            # Create a prompt for Ollama to structure the data
            source = article.get('source', self.source_name)
            prompt = f"""You are a data structuring assistant. Given the following scraped article data from {source}, 
please clean and structure it into a proper JSON format with these fields:
- title (string): The article title
- url (string): The article URL
- description (string): A brief description or excerpt (1-2 sentences). If no description is provided in the raw data, generate one based on the title and context.
- author (string): The author name (if available, otherwise empty string)
- published_date (string): Publication date in ISO format if possible
- category (string): Choose ONLY ONE category from this exact list: "Trending", "Technology", "Education", "Careers", "AI & ML". Pick the most appropriate one based on the article's content.
- tags (array): Extract 3-5 relevant tags/keywords from the title and description

CRITICAL RULES:
1. The description field must NEVER be empty. If the raw data has no description, create a brief 1-2 sentence description based on the title.
2. The tags array must contain at least 3 relevant keywords extracted from the title/description.
3. The category field MUST be exactly one of these values: "Trending", "Technology", "Education", "Careers", "AI & ML"
   - Use "Technology" for general tech news, gadgets, devices, software, apps, companies
   - Use "AI & ML" for artificial intelligence, machine learning, neural networks, AI tools
   - Use "Education" for learning, educational tech, online courses, student-related content
   - Use "Careers" for job-related, workplace, professional development content
   - Use "Trending" for viral content, breaking news, or topics that don't fit other categories

Raw data:
{json.dumps(article, indent=2)}

Return ONLY valid JSON, no explanation or markdown formatting."""

            try:
                # Call Ollama API
                response = ollama.chat(
                    model=self.ollama_model,
                    messages=[
                        {
                            'role': 'user',
                            'content': prompt
                        }
                    ]
                )
                
                # Extract the response content
                structured_content = response['message']['content']
                
                # Try to parse as JSON with robust extraction
                try:
                    # Remove markdown code blocks if present
                    if '```json' in structured_content:
                        structured_content = structured_content.split('```json')[1].split('```')[0].strip()
                    elif '```' in structured_content:
                        structured_content = structured_content.split('```')[1].split('```')[0].strip()
                    
                    # Extract JSON object from response - find first { and last }
                    json_start = structured_content.find('{')
                    json_end = structured_content.rfind('}')
                    
                    if json_start != -1 and json_end != -1 and json_start < json_end:
                        structured_content = structured_content[json_start:json_end+1].strip()
                    
                    structured_article = json.loads(structured_content)
                    
                    # Validate required fields with strict rules, use original data as fallback
                    if not structured_article.get('title'):
                        structured_article['title'] = article.get('title', 'Untitled')
                    if not structured_article.get('url'):
                        structured_article['url'] = article.get('url', '')
                    
                    # Description validation - must not be empty
                    description = structured_article.get('description', '').strip()
                    if not description or len(description) < 10:
                        # Try original description
                        original_desc = article.get('description', '').strip()
                        if original_desc and len(original_desc) >= 10:
                            structured_article['description'] = original_desc
                        else:
                            # Generate from title as last resort
                            title = structured_article.get('title', '')
                            structured_article['description'] = f"Article about {title.lower()}" if title else "No description available"
                    
                    # Tags validation - must have at least 3 tags
                    tags = structured_article.get('tags', [])
                    if not tags or len(tags) < 3:
                        # Generate basic tags from title
                        title_words = structured_article.get('title', '').lower().split()
                        # Filter out common words
                        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'from', 'is', 'are', 'was', 'were'}
                        meaningful_words = [w for w in title_words if w not in stop_words and len(w) > 3][:5]
                        structured_article['tags'] = meaningful_words if meaningful_words else [source]
                    
                    if not structured_article.get('author'):
                        structured_article['author'] = article.get('author', '')
                    if not structured_article.get('published_date'):
                        structured_article['published_date'] = article.get('published_date', None)
                    if not structured_article.get('category'):
                        structured_article['category'] = 'Trending'
                    
                    # Fetch thumbnail for the article
                    print(f"  → Fetching thumbnail...")
                    thumbnail = get_article_thumbnail(
                        structured_article.get('title', ''),
                        structured_article.get('category')
                    )
                    
                    if thumbnail:
                        structured_article['thumbnail'] = thumbnail
                        print(f"  ✓ Thumbnail added")
                    else:
                        structured_article['thumbnail'] = None
                        print(f"  ✗ No thumbnail found")
                    
                    structured_articles.append(structured_article)
                except (json.JSONDecodeError, ValueError) as e:
                    print(f"  Warning: Could not parse Ollama response for article {idx}: {str(e)[:50]}")
                    # Use original data with all available fields
                    enriched_article = {
                        'title': article.get('title', 'Untitled'),
                        'url': article.get('url', ''),
                        'description': article.get('description', ''),
                        'author': article.get('author', ''),
                        'published_date': article.get('published_date', None),
                        'category': 'Trending',
                        'tags': article.get('tags', []),
                        'source': article.get('source', self.source_name)
                    }
                    
                    # Fetch thumbnail
                    thumbnail = get_article_thumbnail(
                        enriched_article.get('title', ''),
                        enriched_article.get('category')
                    )
                    enriched_article['thumbnail'] = thumbnail
                    
                    structured_articles.append(enriched_article)
                
            except Exception as e:
                print(f"  Error processing with Ollama: {e}")
                # Fall back to original article data
                article['thumbnail'] = None
                structured_articles.append(article)
        
        return structured_articles
    
    def save_to_json(self, data: List[Dict], filename: str = "articles.json", source: str = None):
        """Save structured data to JSON file."""
        output = {
            'source': source or self.source_name,
            'scraped_at': datetime.now().isoformat(),
            'total_articles': len(data),
            'articles': data
        }
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(output, f, indent=2, ensure_ascii=False)
        
        print(f"\n✓ Data saved to {filename}")
        print(f"✓ Total articles: {len(data)}")
    
    def run(self, output_file: str = "verge_articles.json"):
        """Run the complete scraping and processing pipeline."""
        try:
            # Step 1: Fetch the page
            soup = self.fetch_page()
            
            # Step 2: Extract articles
            articles = self.extract_articles(soup)
            print(f"\n✓ Extracted {len(articles)} articles")
            
            if not articles:
                print("No articles found. The website structure may have changed.")
                return
            
            # Step 3: Structure with Ollama
            structured_articles = self.structure_with_ollama(articles)
            
            # Step 4: Add source to each article
            for article in structured_articles:
                if 'source' not in article:
                    article['source'] = self.source_name
            
            # Step 5: Save to JSON
            self.save_to_json(structured_articles, output_file)
            
            return structured_articles
            
        except requests.RequestException as e:
            print(f"Error fetching page: {e}")
        except Exception as e:
            print(f"An error occurred: {e}")
            raise


def main():
    """Main function to run the scraper."""
    print("="*60)
    print("Tech News Scraper with Ollama AI Processing")
    print("="*60)
    
    all_articles = []
    
    # Scrape The Verge
    print("\n[1/3] Scraping The Verge...")
    print("-"*60)
    verge_scraper = NewsScraperWithAI(
        base_url="https://www.theverge.com/",
        source_name="The Verge"
    )
    verge_articles = verge_scraper.run(output_file="temp_verge.json")
    if verge_articles:
        all_articles.extend(verge_articles)
    
    # Scrape TechCrunch
    print("\n[2/3] Scraping TechCrunch...")
    print("-"*60)
    techcrunch_scraper = NewsScraperWithAI(
        base_url="https://techcrunch.com/latest/",
        source_name="TechCrunch"
    )
    techcrunch_articles = techcrunch_scraper.run(output_file="temp_techcrunch.json")
    if techcrunch_articles:
        all_articles.extend(techcrunch_articles)
    
    # Scrape CNET
    print("\n[3/3] Scraping CNET...")
    print("-"*60)
    cnet_scraper = NewsScraperWithAI(
        base_url="https://www.cnet.com/",
        source_name="CNET"
    )
    cnet_articles = cnet_scraper.run(output_file="temp_cnet.json")
    if cnet_articles:
        all_articles.extend(cnet_articles)
    
    # Combine all articles into one file
    print("\n" + "="*60)
    print("Combining all articles...")
    print("="*60)
    
    combined_output = {
        'sources': ['The Verge', 'TechCrunch', 'CNET'],
        'scraped_at': datetime.now().isoformat(),
        'total_articles': len(all_articles),
        'articles': all_articles
    }
    
    with open('all_articles.json', 'w', encoding='utf-8') as f:
        json.dump(combined_output, f, indent=2, ensure_ascii=False)
    
    print(f"\n✓ Combined data saved to all_articles.json")
    print(f"✓ Total articles from all sources: {len(all_articles)}")
    print(f"  - The Verge: {len(verge_articles) if verge_articles else 0}")
    print(f"  - TechCrunch: {len(techcrunch_articles) if techcrunch_articles else 0}")
    print(f"  - CNET: {len(cnet_articles) if cnet_articles else 0}")
    
    # Clean up temp files
    import os
    for temp_file in ['temp_verge.json', 'temp_techcrunch.json', 'temp_cnet.json']:
        if os.path.exists(temp_file):
            os.remove(temp_file)


if __name__ == "__main__":
    main()
