import json
import requests
import time
import re
import sys

BOT_TOKEN = '8939723654:AAHxjv7bQ4R3hnDXNuacENxaSdh2Y4yF7F0'
TARGET_CHANNEL = '@FOOTBALLWORLDWIDE1'

try:
    with open('news.json', 'r', encoding='utf-8') as f:
        posts = json.load(f)[:4]
    
    for post in reversed(posts):
        text = f"🚨 <b>{post['title']}</b>\n\n{post['text']}\n\n📰 <i>Source: {post['source']}</i>\n🔗 <a href='{post['link']}'>Read More</a>"
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
        time.sleep(2)
        
    with open('index.html', 'r', encoding='utf-8') as f:
        content = f.read()
        
    fallback_js = 'const baseFallback = ' + json.dumps(posts, ensure_ascii=False, indent=4) + ';'
    
    new_content = re.sub(r'const baseFallback = \[.*?\];', fallback_js, content, flags=re.DOTALL)
    
    with open('index.html', 'w', encoding='utf-8') as f:
        f.write(new_content)
except Exception as e:
    pass
