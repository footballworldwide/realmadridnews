import os
import re
import json
import time
import requests
from bs4 import BeautifulSoup

# ==================== CONFIGURATION ====================
SOURCE_CHANNELS = ["https://t.me/s/FabrizioRomano", "https://t.me/s/espnfc", "https://t.me/s/publicgift1"]  # Sources to scrape news from
TARGET_CHANNEL = "@FOOTBALLWORLDWIDE1"        # Your channel username (must start with @)
BOT_TOKEN = "8939723654:AAHxjv7bQ4R3hnDXNuacENxaSdh2Y4yF7F0"         # Get this from @BotFather in Telegram
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

def init_sent_posts():
    print("Eski xabarlar o'qilmoqda... Ular kanalga yuborilmaydi.")
    sent_posts = set()
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    for source in SOURCE_CHANNELS:
        try:
            response = requests.get(source, headers=headers, timeout=15)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, "html.parser")
                messages = soup.find_all("div", class_="tgme_widget_message")
                for msg in messages:
                    post_id = msg.get("data-post")
                    if not post_id:
                        link_el = msg.find("a", class_="tgme_widget_message_date")
                        if link_el and "href" in link_el.attrs:
                            post_id = link_el["href"].split("/")[-1]
                    if post_id:
                        sent_posts.add(post_id)
        except Exception:
            pass
    save_sent_posts(sent_posts)
    print(f"Jami {len(sent_posts)} ta eski xabar bazaga qo'shildi va ular e'tiborsiz qoldiriladi.")

def send_to_telegram(text, image_url=None):
    """Sends message to the target channel using Telegram Bot API"""
    if BOT_TOKEN == "YOUR_TELEGRAM_BOT_TOKEN":
        print("[WARNING] Please configure your BOT_TOKEN in auto_poster.py first!")
        return False

    # Limit text to Telegram caption size limits (1024 chars for captions, 4096 for text)
    caption = text
    if len(caption) > 1000:
        caption = caption[:997] + "..."

    try:
        if image_url:
            # Send photo with caption
            url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto"
            payload = {
                "chat_id": TARGET_CHANNEL,
                "photo": image_url,
                "caption": caption
            }
            res = requests.post(url, json=payload, timeout=15)
        else:
            # Send text message only
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
            # If photo failed, try sending text only as fallback
            if image_url:
                print("Retrying with text only...")
                return send_to_telegram(text, None)
            return False
            
    except Exception as e:
        print(f"Error sending to Telegram: {e}")
        return False

def scrape_and_post():
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }

    for source in SOURCE_CHANNELS:
        print(f"Scraping {source} to forward new posts to {TARGET_CHANNEL}...")
        try:
            response = requests.get(source, headers=headers, timeout=15)
            if response.status_code != 200:
                print(f"Error fetching channel {source}: {response.status_code}")
                continue
                
            soup = BeautifulSoup(response.text, "html.parser")
            messages = soup.find_all("div", class_="tgme_widget_message")
            
            sent_posts = load_sent_posts()
            new_posts_count = 0
            
            # Process from oldest to newest in the scraped batch to post chronologically
            for msg in messages:
                # Extract unique post ID from Telegram post link or data-post attribute
                post_id = msg.get("data-post")
                if not post_id:
                    # Fallback check
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
                    # Small delay to respect Telegram rate limits
                    time.sleep(3)
                    
            print(f"Scrape completed for {source}. Forwarded {new_posts_count} new posts.")
            
        except Exception as e:
            print(f"Error during scrape and post for {source}: {e}")

if __name__ == "__main__":
    print("Auto-poster script started.")
    
    if not os.path.exists(SENT_POSTS_FILE):
        init_sent_posts()
        
    # Run loop
    try:
        while True:
            scrape_and_post()
            print("Sleeping for 15 minutes before checking for new posts...")
            time.sleep(900)  # Check every 15 minutes
    except KeyboardInterrupt:
        print("Auto-poster stopped by user.")
