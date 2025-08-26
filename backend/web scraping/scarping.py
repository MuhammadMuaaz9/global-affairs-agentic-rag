import requests
from bs4 import BeautifulSoup
import json
import os
from urllib.parse import urlparse

from urllib.parse import urlencode
from newspaper import Article
from newspaper import fulltext

API_KEY = ""  # ScraperAPI key
URLS_FILE = "urls.txt"
JSON_FILE = "reuters_articles.json"

# --- Helper: Extract slug from URL ---
def get_slug(url):
    path = urlparse(url).path
    slug = path.strip("/").split("/")[-1] or "article"
    return slug

# --- Load all URLs from file ---
if not os.path.exists(URLS_FILE):
    print(f"{URLS_FILE} not found!")
    exit()

with open(URLS_FILE, "r", encoding="utf-8") as f:
    urls = [line.strip() for line in f if line.strip()]

print(f"Loaded {len(urls)} URLs from {URLS_FILE}")

# --- Load existing JSON if available ---
if os.path.exists(JSON_FILE):
    with open(JSON_FILE, "r", encoding="utf-8") as f:
        try:
            all_articles = json.load(f)
        except json.JSONDecodeError:
            all_articles = []
else:
    all_articles = []

os.makedirs("reuters_articles_html", exist_ok=True)
# --- Process each URL ---
for target_url in urls:
    slug = get_slug(target_url)
    html_filename = os.path.join("reuters_articles_html", f"{slug}.html")

    # Skip if already scraped
    if any(article.get("url") == target_url for article in all_articles):
        print(f"Skipping already scraped: {target_url}")
        continue

    print(f"Fetching: {target_url}")
    payload = {
        'api_key': API_KEY,
        'url': target_url
    }

    article = Article(target_url)

    try:
        response = requests.get('https://api.scraperapi.com', params=urlencode(payload))
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"Error fetching {target_url}: {e}")
        continue

    html = response.text

    # Save raw HTML
    with open(html_filename, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"HTML saved: {html_filename}")

    ## Insert HTML into the Newspaper3k article object and parse the article
    input_html = response.text
    article.download(input_html)
    article.parse()

    text = fulltext(response.text)

    title = article.title
    # Convert datetime to string if not None
    publication_date = (
        article.publish_date.isoformat() if article.publish_date else None
    )

    full_text = " ".join(text.split())

    # Structured data
    article_data = {
        "title": title,
        "publication_date": publication_date,
        "url": target_url,
        "full_text": full_text
    }

    all_articles.append(article_data)
    print(f"Article scraped: {title}")

    with open(JSON_FILE, "w", encoding="utf-8") as f:
        json.dump(all_articles, f, indent=2, ensure_ascii=False)

# --- Save all structured data ---
print(f"All articles saved to {JSON_FILE}")