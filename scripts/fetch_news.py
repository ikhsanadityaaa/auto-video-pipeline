import feedparser
import argparse
import json
import os
import re
from urllib.parse import quote_plus, unquote, parse_qs
from datetime import datetime, timedelta

# === SETTINGS ===
HISTORY_FILE = "data/news_history.json"
BLOCKED_DOMAINS = [
    "blogspot", "wordpress", "medium.com", "substack",
    "facebook.com", "instagram.com", "tiktok.com", "pinterest.com",
    "twitter.com", "x.com", "reddit.com", "quora.com",
    "/blog/", "/opinion/", "forum"
]

# === UTILS ===
def load_history():
    if not os.path.exists(HISTORY_FILE):
        return set()
    try:
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            return set(json.load(f))
    except:
        return set()

def save_history(history_set):
    os.makedirs("data", exist_ok=True)
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(list(history_set), f, indent=2)

def clean_html(text):
    if not text:
        return ""
    text = re.sub(r"<.*?>", " ", text)
    return text.replace("&nbsp;", " ").strip()

def is_blocked(url):
    low = url.lower()
    return any(bad in low for bad in BLOCKED_DOMAINS)

def extract_real_url(google_url):
    if "url=" in google_url:
        try:
            qs = parse_qs(google_url.split("?", 1)[1])
            if "url" in qs:
                return unquote(qs["url"][0])
        except:
            pass
    return google_url

def fetch_feed(keyword):
    q = quote_plus(keyword)
    url = f"https://news.google.com/rss/search?q={q}&hl=en&gl=US&ceid=US:en"
    return feedparser.parse(url)

# === MAIN LOGIC ===
def find_one_article(keywords):
    history = load_history()
    windows = [1, 7, 30, 365]  # hari
    for days in windows:
        print(f"=== CARI BERITA {days}-HARI ===")
        for kw in keywords:
            feed = fetch_feed(kw)
            for e in feed.entries:
                if "published_parsed" not in e:
                    continue
                pub = datetime(*e.published_parsed[:6])
                cutoff = datetime.utcnow() - timedelta(days=days)
                if pub < cutoff:
                    continue
                real_link = extract_real_url(e.link)
                if is_blocked(real_link):
                    continue
                if real_link in history:
                    continue
                return {
                    "keyword": kw,
                    "title": clean_html(e.title),
                    "link": real_link,
                    "summary": clean_html(e.summary) if "summary" in e else "",
                    "published": pub.isoformat()
                }
    return None

# === RUN ===
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--keywords-file", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()

    with open(args.keywords-file, "r", encoding="utf-8") as f:
        keywords = [k.strip() for k in f if k.strip()]

    article = find_one_article(keywords)

    if article:
        print("✅ BERITA DITEMUKAN")
        print(f"Judul   : {article['title']}")
        print(f"Link    : {article['link']}")
        print(f"Keyword : {article['keyword']}")

        with open(args.out, "w", encoding="utf-8") as f:
            json.dump(article, f, indent=2, ensure_ascii=False)

        history = load_history()
        history.add(article["link"])
        save_history(history)
    else:
        print("❌ TIDAK ADA BERITA YANG COCOK")
        with open(args.out, "w", encoding="utf-8") as f:
            json.dump({"error": "no_news"}, f, indent=2)
