import feedparser
import argparse
import json
import os
from datetime import datetime, timedelta
from urllib.parse import quote_plus
import re

# Lokasi penyimpanan riwayat berita agar tidak terpakai ulang
HISTORY_FILE = "data/news_history.json"

# Kata yang menandakan BLOG, FORUM, atau bukan media berita
BLOG_MARKERS = [
    "blog",
    "medium.com",
    "wordpress",
    "blogspot",
    "substack",
    "tumblr",
    "forum"
]

def is_blog(url):
    url = url.lower()
    return any(b in url for b in BLOG_MARKERS)

def clean_html(text):
    text = re.sub("<.*?>", "", text)
    text = text.replace("&nbsp;", " ").replace("&amp;", "&")
    return text.strip()

def load_history():
    if not os.path.exists(HISTORY_FILE):
        return []
    try:
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return []

def save_history(history):
    os.makedirs("data", exist_ok=True)
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(history, f, indent=2)

def fetch_news(keyword, days):
    q = quote_plus(keyword)
    url = f"https://news.google.com/rss/search?q={q}&hl=en&gl=US&ceid=US:en"
    feed = feedparser.parse(url)

    now = datetime.utcnow()
    limit = now - timedelta(days=days)
    history = load_history()

    for entry in feed.entries:
        if "published_parsed" not in entry:
            continue

        pub = datetime(*entry.published_parsed[:6])
        if pub < limit:
            continue

        link = entry.link.lower()

        if is_blog(link):
            continue

        title = clean_html(entry.title)
        summary = clean_html(entry.summary) if "summary" in entry else ""

        # Jangan pakai berita yang sudah dipakai
        if link in history:
            continue

        return {
            "keyword": keyword,
            "title": title,
            "summary": summary,
            "link": link,
            "published": pub.isoformat()
        }

    return None

def search_with_fallback(keywords):
    print("Mencari berita dalam 24 jam terakhir")
    for kw in keywords:
        result = fetch_news(kw, 1)
        if result:
            return result

    print("Tidak ada. Coba dalam 7 hari")
    for kw in keywords:
        result = fetch_news(kw, 7)
        if result:
            return result

    print("Tidak ada. Coba dalam 30 hari")
    for kw in keywords:
        result = fetch_news(kw, 30)
        if result:
            return result

    print("Tidak ada juga. Coba artikel lama")
    for kw in keywords:
        result = fetch_news(kw, 3650)  # 10 tahun
        if result:
            return result

    return None

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--keywords-file", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()

    with open(args.keywords_file, "r", encoding="utf-8") as f:
        keywords = [x.strip() for x in f.readlines() if x.strip()]

    result = search_with_fallback(keywords)

    if result:
        print("=== BERITA DITEMUKAN ===")
        print("Keyword :", result["keyword"])
        print("Judul   :", result["title"])
        print("Link    :", result["link"])
        print("Ringkas :", result["summary"])

        history = load_history()
        history.append(result["link"])
        save_history(history)

        with open(args.out, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
    else:
        print("=== TIDAK ADA SATUPUN BERITA YANG COCOK ===")
        with open(args.out, "w", encoding="utf-8") as f:
            json.dump({"error": "no_news_found"}, f, indent=2)
