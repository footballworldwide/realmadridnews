"""
AI Pulse — Inject initial data to Telegram and update fallback content.
Run this once to seed the Telegram channel with the first batch of news.
"""
import json
import os
import requests
import time

BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TARGET_CHANNEL = os.environ.get("TELEGRAM_CHANNEL", "@AINEWSHUB0")

if not BOT_TOKEN:
    print("⚠️  TELEGRAM_BOT_TOKEN not set!")
    print("Set it: set TELEGRAM_BOT_TOKEN=your_token_here")
    exit(1)

try:
    with open('news.json', 'r', encoding='utf-8') as f:
        posts = json.load(f)[:4]

    print(f"📡 Sending {len(posts)} articles to {TARGET_CHANNEL}...")

    for post in reversed(posts):
        text = (
            f"🤖 <b>{post['title']}</b>\n\n"
            f"{post['text']}\n\n"
            f"📡 <i>Source: {post['source']}</i>\n"
            f"🔗 <a href='{post['link']}'>Read Full Article</a>"
        )
        if len(text) > 1000:
            text = text[:990] + "...</a>"

        url = f'https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto'
        payload = {
            'chat_id': TARGET_CHANNEL,
            'photo': post['image_url'],
            'caption': text,
            'parse_mode': 'HTML'
        }
        res = requests.post(url, json=payload, timeout=15)
        result = res.json()
        if result.get('ok'):
            print(f"   ✅ {post['title'][:50]}...")
        else:
            print(f"   ❌ Failed: {result.get('description')}")
        time.sleep(2)

    print("\n✅ Done! Initial posts sent to Telegram.")

except FileNotFoundError:
    print("❌ news.json not found! Run scraper.py first.")
except Exception as e:
    print(f"❌ Error: {e}")
