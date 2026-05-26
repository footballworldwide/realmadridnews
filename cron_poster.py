import os
import re
import json
import time
import requests
from bs4 import BeautifulSoup

# ==================== CONFIGURATION ====================
SOURCE_CHANNEL = "https://t.me/s/realmadrid"  # Source to scrape news from
TARGET_CHANNEL = "@RealMadridNews1000"        # Your channel username (must start with @)
# The Telegram Bot Token will be read securely from GitHub Secrets
BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
# =======================================================

SENT_POSTS_FILE = "sent_posts.json"

def load_sent_posts():
    if os.path.exists(SENT_POSTS_FILE):
        try:
            with open(SENT_POSTS_FILE, "r", encoding="utf-8") as f:
                return set(json.load(f))
        except Exception:
            return set()
    return set()

def save_sent_posts(sent_ids):
    with open(SENT_POSTS_FILE, "w", encoding="utf-8") as f:
        json.dump(list(sent_ids), f, ensure_ascii=False, indent=4)

def send_to_telegram(text, image_url=None):
    """Sends message to the target channel using Telegram Bot API"""
    if not BOT_TOKEN:
        print("[ERROR] TELEGRAM_BOT_TOKEN environment variable is not set!")
        return False

    caption = text
    if len(caption) > 1000:
        caption = caption[:997] + "..."

    try:
        if image_url:
            url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto"
            payload = {
                "chat_id": TARGET_CHANNEL,
                "photo": image_url,
                "caption": caption
            }
            res = requests.post(url, json=payload, timeout=15)
        else:
            url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
            payload = {
                "chat_id": TARGET_CHANNEL,
                "text": caption
            }
            res = requests.post(url, json=payload, timeout=15)

        response_data = res.json()
        if response_data.get("ok"):
            print("Successfully posted to Telegram channel!")
            return True
        else:
            print(f"Failed to post: {response_data.get('description')}")
            if image_url:
                print("Retrying with text only...")
                return send_to_telegram(text, None)
            return False
            
    except Exception as e:
        print(f"Error sending to Telegram: {e}")
        return False

def scrape_and_post():
    print(f"Scraping {SOURCE_CHANNEL} to forward new posts to {TARGET_CHANNEL}...")
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }

    try:
        response = requests.get(SOURCE_CHANNEL, headers=headers, timeout=15)
        if response.status_code != 200:
            print(f"Error fetching channel: {response.status_code}")
            return
            
        soup = BeautifulSoup(response.text, "html.parser")
        messages = soup.find_all("div", class_="tgme_widget_message")
        
        sent_posts = load_sent_posts()
        new_posts_count = 0
        
        # Process from oldest to newest in the scraped batch to post chronologically
        for msg in messages:
            post_id = msg.get("data-post")
            if not post_id:
                link_el = msg.find("a", class_="tgme_widget_message_date")
                if link_el and "href" in link_el.attrs:
                    post_id = link_el["href"].split("/")[-1]
            
            if not post_id or post_id in sent_posts:
                continue
                
            # Extract text
            text_el = msg.find("div", class_="tgme_widget_message_text")
            if not text_el:
                continue
            text = text_el.get_text(separator="\n").strip()
            
            # Extract image
            img_url = None
            photo_el = msg.find("a", class_="tgme_widget_message_photo_wrap")
            if photo_el and "style" in photo_el.attrs:
                style_attr = photo_el["style"]
                match = re.search(r"background-image:url\(['\"]?(.*?)['\"]?\)", style_attr)
                if match:
                    img_url = match.group(1)
            
            print(f"Found new post [{post_id}]. Forwarding...")
            
            # Post to Channel
            success = send_to_telegram(text, img_url)
            if success:
                sent_posts.add(post_id)
                new_posts_count += 1
                save_sent_posts(sent_posts)
                time.sleep(3)
                
        print(f"Scrape completed. Forwarded {new_posts_count} new posts.")
        
    except Exception as e:
        print(f"Error during scrape and post: {e}")

if __name__ == "__main__":
    # Runs exactly once per execution (ideal for Cron / GitHub Actions)
    scrape_and_post()
