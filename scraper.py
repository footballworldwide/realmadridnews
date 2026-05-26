import os
import re
import json
import time
import requests
from bs4 import BeautifulSoup
from datetime import datetime

# Settings
CHANNEL_URL = "https://t.me/s/RealMadridNews1000"
JSON_FILE = "news.json"

def scrape_telegram_news():
    print(f"Scraping latest news from {CHANNEL_URL}...")
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    
    try:
        response = requests.get(CHANNEL_URL, headers=headers, timeout=15)
        if response.status_code != 200:
            print(f"Error: Status code {response.status_code}")
            return False
            
        soup = BeautifulSoup(response.text, "html.parser")
        # Find all message blocks
        messages = soup.find_all("div", class_="tgme_widget_message")
        
        posts = []
        # Process in reverse to get newest first if they are ordered chronologically
        for msg in reversed(messages):
            if len(posts) >= 10:
                break
                
            # 1. Text content
            text_el = msg.find("div", class_="tgme_widget_message_text")
            if not text_el:
                continue # Skip if no text
                
            text = text_el.get_text(separator="\n").strip()
            # Title is the first line or first 60 chars
            lines = [l.strip() for l in text.split("\n") if l.strip()]
            title = lines[0] if lines else "Real Madrid News Update"
            if len(title) > 80:
                title = title[:77] + "..."
            
            # 2. Image URL
            img_url = None
            photo_el = msg.find("a", class_="tgme_widget_message_photo_wrap")
            if photo_el and "style" in photo_el.attrs:
                style_attr = photo_el["style"]
                match = re.search(r"background-image:url\(['\"]?(.*?)['\"]?\)", style_attr)
                if match:
                    img_url = match.group(1)
            
            # 3. Date
            date_el = msg.find("time", class_="time")
            post_date = ""
            if date_el and "datetime" in date_el.attrs:
                dt_str = date_el["datetime"]
                try:
                    # e.g., 2026-05-26T09:18:20+00:00
                    dt = datetime.fromisoformat(dt_str)
                    post_date = dt.strftime("%Y-%m-%d %H:%M")
                except Exception:
                    post_date = dt_str
            else:
                post_date = datetime.now().strftime("%Y-%m-%d %H:%M")
                
            posts.append({
                "title": title,
                "text": text,
                "image_url": img_url or "https://images.unsplash.com/photo-1508098682722-e99c43a406b2?auto=format&fit=crop&w=800&q=80",
                "date": post_date
            })
            
        if not posts:
            print("No posts found. Using fallback RSS/Mock data...")
            # Fallback to prevent empty site
            posts = get_fallback_posts()
            
        with open(JSON_FILE, "w", encoding="utf-8") as f:
            json.dump(posts, f, ensure_ascii=False, indent=4)
            
        print(f"Successfully saved {len(posts)} posts to {JSON_FILE}")
        return True
        
    except Exception as e:
        print(f"Exception occurred during scraping: {e}")
        # Fallback
        try:
            with open(JSON_FILE, "w", encoding="utf-8") as f:
                json.dump(get_fallback_posts(), f, ensure_ascii=False, indent=4)
            print("Saved fallback posts due to scraper error.")
        except Exception:
            pass
        return False

def get_fallback_posts():
    return [
        {
            "title": "Welcome to the Premium Real Madrid News Feed!",
            "text": "This feed automatically displays the latest updates, match analysis, and transfer news about the greatest club in the world. Hala Madrid!",
            "image_url": "https://images.unsplash.com/photo-1508098682722-e99c43a406b2?auto=format&fit=crop&w=1200&q=80",
            "date": datetime.now().strftime("%Y-%m-%d %H:%M")
        },
        {
            "title": "Mbappe Shines in Training Ahead of Next Clash",
            "text": "Kylian Mbappe was seen scoring brilliant goals in the training session today as Real Madrid prepares for the upcoming match. The squad looks highly motivated.",
            "image_url": "https://images.unsplash.com/photo-1540747737956-37872404a821?auto=format&fit=crop&w=800&q=80",
            "date": datetime.now().strftime("%Y-%m-%d %H:%M")
        },
        {
            "title": "Ancelotti: 'We are ready for the final matches'",
            "text": "Carlo Ancelotti addressed the media in today's press conference: 'The team is physically in great shape and we are fully focused on taking home the trophies.'",
            "image_url": "https://images.unsplash.com/photo-1574629810360-7efbbe195018?auto=format&fit=crop&w=800&q=80",
            "date": datetime.now().strftime("%Y-%m-%d %H:%M")
        },
        {
            "title": "Santiago Bernabeu Renovation Updates",
            "text": "The legendary stadium is looking more futuristic than ever. Check out the latest pictures of the new retractable pitch technology and 360-degree screen.",
            "image_url": "https://images.unsplash.com/photo-1522771739844-6a9f6d5f14af?auto=format&fit=crop&w=800&q=80",
            "date": datetime.now().strftime("%Y-%m-%d %H:%M")
        }
    ]

if __name__ == "__main__":
    # Run once immediately
    scrape_telegram_news()
    
    # Loop to run every 10 minutes (600 seconds)
    print("Scraper is now running in loop mode. Press Ctrl+C to stop.")
    try:
        while True:
            time.sleep(600)
            scrape_telegram_news()
    except KeyboardInterrupt:
        print("Scraper stopped by user.")
