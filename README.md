# Tech News Scraper with Ollama AI

A web scraping tool that fetches articles from **The Verge** and **TechCrunch**, then uses Ollama AI to structure and categorize the data before storing it in JSON format.

## Features

- Scrapes articles from multiple tech news sources:
  - **The Verge** (theverge.com)
  - **TechCrunch** (techcrunch.com/latest/)
  - **CNET** (cnet.com)
- Extracts titles, URLs, descriptions, authors, and publication dates
- Uses Ollama AI to clean and structure the data
- Automatically categorizes content into predefined categories:
  - **Trending** - Viral content, breaking news
  - **Technology** - Gadgets, devices, software, companies
  - **Education** - Learning, educational tech, courses
  - **Careers** - Jobs, workplace, professional development
  - **AI & ML** - Artificial intelligence, machine learning
- Extracts relevant tags/keywords
- Combines results from all sources into a single JSON file

## Requirements

- Python 3.7+
- Ollama installed locally with a model (e.g., llama3.2)
- Internet connection

## Installation

1. Make sure Ollama is installed and running:
   - Download from https://ollama.com/
   - Pull a model: `ollama pull llama3.2`

2. Install Python dependencies (already done in virtual environment):
   ```bash
   pip install requests beautifulsoup4 lxml ollama
   ```

## Usage

Run the scraper:

```bash
python main.py
```

Or from the virtual environment:

```bash
D:/academix/scraper/vtps/Scripts/python.exe main.py
```

## Output

The scraper creates `all_articles.json` with structured data from all sources:

```json
{
  "sources": ["The Verge", "TechCrunch", "CNET"],
  "scraped_at": "2025-12-01T...",
  "total_articles": 55,
  "articles": [
    {
      "title": "Article title",
      "url": "https://...",
      "description": "Article description",
      "author": "Author name",
      "published_date": "2025-12-01T...",
      "category": "Technology",
      "tags": ["tag1", "tag2", "tag3"],
      "source": "The Verge"
    }
  ]
}
```

## Configuration

You can modify the scraper behavior in `main.py`:

- Change the Ollama model: Update `model='llama3.2:3b'` to your preferred model
- Adjust article limit per source: Modify `[:20]` in the extraction methods
- Add more sources: Create new scraper instances in the `main()` function
- Modify categories: Update the category list in the Ollama prompt

## Notes

- The scraper limits to ~20 articles per source (~55 total) by default
- Processing each article with AI takes a few seconds
- Make sure Ollama is running before executing the script
- Articles are categorized into: Trending, Technology, Education, Careers, or AI & ML
