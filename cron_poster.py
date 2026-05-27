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
    print(f"✅ Marked {len(sent_posts)} existing posts as sent.")


def send_to_telegram(post):
    if not BOT_TOKEN:
        print("[⚠️] BOT_TOKEN is not set! Set TELEGRAM_BOT_TOKEN environment variable.")
        return False

    text = (
        f"🤖 <b>{post['title']}</b>\n\n"
        f"{post['text']}\n\n"
        f"📡 <i>Source: {post['source']}</i>\n"
        f"🔗 <a href='{post['link']}'>Read Full Article</a>"
    )

    if len(text) > 1000:
        text = text[:990] + "...</a>"

    try:
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
    print("🔍 Checking for new AI news to forward to Telegram...")
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

    for post in reversed(posts):
        post_id = post.get("id")
        if not post_id or post_id in sent_posts:
            continue

        success = send_to_telegram(post)
        if success:
            sent_posts.add(post_id)
            new_posts_count += 1
            save_sent_posts(sent_posts)
            time.sleep(3)

    if new_posts_count > 0:
        print(f"🚀 Posted {new_posts_count} new AI articles to Telegram.")
    else:
        print("ℹ️  No new articles to post.")


if __name__ == "__main__":
    """Runs once per execution — designed for GitHub Actions cron."""
    print("=" * 50)
    print("  AI Pulse — Cron Poster (Single Run)")
    print("=" * 50)

    if not BOT_TOKEN:
        print("\n⚠️  WARNING: TELEGRAM_BOT_TOKEN is not set!")
        print("Add it as a GitHub secret or set the environment variable.\n")

    if not os.path.exists(SENT_POSTS_FILE):
        init_sent_posts()

    # Runs exactly once per execution
    post_news()
