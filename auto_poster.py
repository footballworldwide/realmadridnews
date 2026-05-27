import os
import json
import time
import requests

TARGET_CHANNEL = os.environ.get("TELEGRAM_CHANNEL", "@AINEWSHUB0")
BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
SENT_POSTS_FILE = "sent_posts.json"
NEWS_FILE = "news.json"


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
    """Mark existing news as already sent so they won't be re-posted."""
    print("📋 Reading existing posts to avoid re-sending them...")
    sent_posts = set()
    if os.path.exists(NEWS_FILE):
        try:
            with open(NEWS_FILE, "r", encoding="utf-8") as f:
                posts = json.load(f)
                for post in posts:
                    if post.get('id'):
                        sent_posts.add(post['id'])
        except Exception:
            pass
    save_sent_posts(sent_posts)
    print(f"✅ Marked {len(sent_posts)} existing posts as sent. They will be skipped.")


def send_to_telegram(post):
    if not BOT_TOKEN:
        print("[⚠️] BOT_TOKEN is not set! Set TELEGRAM_BOT_TOKEN environment variable.")
        return False

    # Format message with AI-themed emojis
    text = (
        f"🤖 <b>{post['title']}</b>\n\n"
        f"{post['text']}\n\n"
        f"📡 <i>Source: {post['source']}</i>\n"
        f"🔗 <a href='{post['link']}'>Read Full Article</a>"
    )

    # Telegram caption limit is 1024 chars
    if len(text) > 1000:
        text = text[:990] + "...</a>"

    try:
        # Try sending with photo first
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto"
        payload = {
            "chat_id": TARGET_CHANNEL,
            "photo": post['image_url'],
            "caption": text,
            "parse_mode": "HTML"
        }
        res = requests.post(url, json=payload, timeout=15)

        response_data = res.json()
        if response_data.get("ok"):
            print(f"   ✅ Posted: {post['title'][:60]}...")
            return True
        else:
            print(f"   ⚠️  Photo failed: {response_data.get('description')}. Trying text-only...")
            # Fallback to text-only message
            url_text = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
            payload_text = {
                "chat_id": TARGET_CHANNEL,
                "text": text,
                "parse_mode": "HTML",
                "disable_web_page_preview": False
            }
            res_text = requests.post(url_text, json=payload_text, timeout=15)
            if res_text.json().get("ok"):
                print(f"   ✅ Text posted: {post['title'][:60]}...")
                return True
            return False

    except Exception as e:
        print(f"   ❌ Error sending to Telegram: {e}")
        return False


def post_news():
    print("\n🔍 Checking for new AI news to forward to Telegram...")
    if not os.path.exists(NEWS_FILE):
        print("❌ No news.json found. Make sure scraper.py has run first.")
        return

    try:
        with open(NEWS_FILE, "r", encoding="utf-8") as f:
            posts = json.load(f)
    except Exception as e:
        print(f"❌ Error reading news.json: {e}")
        return

    sent_posts = load_sent_posts()
    new_posts_count = 0

    # Reverse to post oldest first (chronological order)
    for post in reversed(posts):
        post_id = post.get("id")
        if not post_id or post_id in sent_posts:
            continue

        success = send_to_telegram(post)
        if success:
            sent_posts.add(post_id)
            new_posts_count += 1
            save_sent_posts(sent_posts)
            time.sleep(3)  # Rate limiting - avoid Telegram flood

    if new_posts_count > 0:
        print(f"\n🚀 Posted {new_posts_count} new AI articles to Telegram.")
    else:
        print("ℹ️  No new articles to post.")


if __name__ == "__main__":
    print("=" * 50)
    print("  AI Pulse — Telegram Auto-Poster")
    print("=" * 50)

    if not BOT_TOKEN:
        print("\n⚠️  WARNING: TELEGRAM_BOT_TOKEN is not set!")
        print("Set it via: set TELEGRAM_BOT_TOKEN=your_token_here")
        print("Or export TELEGRAM_BOT_TOKEN=your_token_here\n")

    if not os.path.exists(SENT_POSTS_FILE):
        init_sent_posts()

    try:
        while True:
            post_news()
            print(f"\n⏳ Sleeping 5 minutes before next check...")
            time.sleep(300)
    except KeyboardInterrupt:
        print("\n🛑 Stopped by user.")
