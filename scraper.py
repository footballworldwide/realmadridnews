import os
import time
import json
import requests
import feedparser
from bs4 import BeautifulSoup
from datetime import datetime

# === AI News RSS Feeds ===
RSS_FEEDS = [
    {"name": "TechCrunch AI", "url": "https://techcrunch.com/category/artificial-intelligence/feed/"},
    {"name": "The Verge", "url": "https://www.theverge.com/rss/ai-artificial-intelligence/index.xml"},
    {"name": "Ars Technica", "url": "https://feeds.arstechnica.com/arstechnica/technology-lab"},
    {"name": "VentureBeat", "url": "https://venturebeat.com/category/ai/feed/"},
]

JSON_FILE = "news.json"
DEFAULT_FALLBACK_IMAGE = "https://images.unsplash.com/photo-1677442136019-21780ecad995?w=800&q=80"

# Keywords to filter AI-related articles (especially for general feeds like Ars Technica)
AI_KEYWORDS = [
    "ai", "artificial intelligence", "machine learning", "deep learning",
    "neural network", "gpt", "llm", "large language model", "chatgpt",
    "openai", "deepmind", "anthropic", "claude", "gemini", "copilot",
    "midjourney", "stable diffusion", "generative ai", "transformer",
    "nlp", "natural language", "computer vision", "robotics", "robot",
    "autonomous", "self-driving", "reinforcement learning", "diffusion model",
    "foundation model", "multimodal", "text-to-image", "text-to-video",
    "ai safety", "alignment", "agi", "superintelligence", "ml model",
    "training data", "inference", "gpu", "nvidia", "tensor", "pytorch",
    "tensorflow", "hugging face", "meta ai", "google ai", "microsoft ai",
    "ai startup", "ai regulation", "ai act", "ai chip", "ai agent",
]


def is_ai_related(title, description):
    """Check if article is AI-related based on keywords in title/description."""
    text = f"{title} {description}".lower()
    return any(keyword in text for keyword in AI_KEYWORDS)


def get_og_image(url):
    """Scrapes the actual article page to find the main meta image (og:image)."""
    try:
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
        res = requests.get(url, timeout=8, headers=headers)
        if res.status_code == 200:
            soup = BeautifulSoup(res.text, "html.parser")
            meta = soup.find("meta", property="og:image")
            if meta and meta.get("content"):
                return meta.get("content")
    except Exception:
        pass
    return None


def fetch_rss_news():
    print("=" * 50)
    print("AI Pulse — Scraping latest AI news from RSS feeds...")
    print("=" * 50)
    all_posts = []

    for feed_info in RSS_FEEDS:
        print(f"\n📡 Fetching from {feed_info['name']}...")
        try:
            feed = feedparser.parse(feed_info['url'])
            count = 0
            for entry in feed.entries[:20]:  # Check top 20 from each feed

                # Extract description
                description = ""
                if hasattr(entry, 'description'):
                    soup = BeautifulSoup(entry.description, "html.parser")
                    description = soup.get_text(separator=" ").strip()

                # For general feeds, filter for AI-related content only
                if feed_info['name'] in ['Ars Technica']:
                    if not is_ai_related(entry.title, description):
                        continue

                image_url = DEFAULT_FALLBACK_IMAGE

                # 1. Extract image from standard media:content
                if hasattr(entry, 'media_content') and len(entry.media_content) > 0:
                    image_url = entry.media_content[0].get('url', image_url)
                elif hasattr(entry, 'media_thumbnail') and len(entry.media_thumbnail) > 0:
                    image_url = entry.media_thumbnail[0].get('url', image_url)
                elif hasattr(entry, 'links'):
                    for link in entry.links:
                        if link.get('type') and link.get('type').startswith('image'):
                            image_url = link.get('href', image_url)

                # 2. Extract image from description HTML
                if image_url == DEFAULT_FALLBACK_IMAGE and hasattr(entry, 'description'):
                    soup_img = BeautifulSoup(entry.description, "html.parser")
                    img = soup_img.find('img')
                    if img and img.get('src'):
                        image_url = img.get('src')

                # 3. Extract from content:encoded
                if image_url == DEFAULT_FALLBACK_IMAGE and hasattr(entry, 'content'):
                    for content in entry.content:
                        soup_content = BeautifulSoup(content.get('value', ''), "html.parser")
                        img = soup_content.find('img')
                        if img and img.get('src'):
                            image_url = img.get('src')
                            break

                # 4. Scrape og:image from article page as last resort
                if image_url == DEFAULT_FALLBACK_IMAGE and hasattr(entry, 'link'):
                    og_img = get_og_image(entry.link)
                    if og_img:
                        image_url = og_img

                # Date parsing
                dt = datetime.now()
                if hasattr(entry, 'published_parsed') and entry.published_parsed:
                    try:
                        dt = datetime.fromtimestamp(time.mktime(entry.published_parsed))
                    except Exception:
                        pass
                elif hasattr(entry, 'updated_parsed') and entry.updated_parsed:
                    try:
                        dt = datetime.fromtimestamp(time.mktime(entry.updated_parsed))
                    except Exception:
                        pass

                post = {
                    "id": entry.get('id', entry.link),
                    "title": entry.title,
                    "text": description[:300] if description else "",
                    "link": entry.link,
                    "image_url": image_url,
                    "date": dt.strftime("%Y-%m-%d %H:%M"),
                    "source": feed_info['name'],
                    "timestamp": dt.timestamp()
                }
                all_posts.append(post)
                count += 1

            print(f"   ✅ Got {count} articles from {feed_info['name']}")
        except Exception as e:
            print(f"   ❌ Error fetching {feed_info['name']}: {e}")

    # Sort posts by date (newest first)
    all_posts.sort(key=lambda x: x['timestamp'], reverse=True)

    # Remove duplicates by title similarity
    seen_titles = set()
    unique_posts = []
    for post in all_posts:
        title_key = post['title'].lower().strip()[:60]
        if title_key not in seen_titles:
            seen_titles.add(title_key)
            unique_posts.append(post)

    # Keep top 50 for the website
    top_posts = unique_posts[:50]

    # Remove timestamp before saving
    for post in top_posts:
        if 'timestamp' in post:
            del post['timestamp']

    if not top_posts:
        print("\n⚠️  No posts found. Using fallback data...")
        top_posts = get_fallback_posts()

    with open(JSON_FILE, "w", encoding="utf-8") as f:
        json.dump(top_posts, f, ensure_ascii=False, indent=4)

    print(f"\n🚀 Successfully saved {len(top_posts)} AI news articles to {JSON_FILE}")
    return True


def get_fallback_posts():
    return [
        {
            "id": "fallback-1",
            "title": "Welcome to AI Pulse — Your Premium AI News Feed",
            "text": "AI Pulse automatically aggregates the latest AI news, breakthroughs, research papers, and startup updates from top tech sources worldwide.",
            "link": "https://openai.com",
            "image_url": DEFAULT_FALLBACK_IMAGE,
            "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "source": "AI Pulse"
        }
    ]


if __name__ == "__main__":
    fetch_rss_news()
    if os.environ.get("GITHUB_ACTIONS") == "true":
        print("\n📦 Running inside GitHub Actions. Exiting after single scrape.")
    else:
        print("\n🔄 Scraper running in loop mode (every 5 minutes). Press Ctrl+C to stop.")
        try:
            while True:
                time.sleep(300)
                fetch_rss_news()
        except KeyboardInterrupt:
            print("\n🛑 Scraper stopped by user.")
