import feedparser
import argparse
import json
from datetime import datetime, timedelta
from urllib.parse import quote_plus
import os
import re

# ====== DETEKSI BLOG (DIBLACKLIST) ======
BLOG_PATTERNS = [
    "blogspot.", "wordpress.", "medium.com", "substack.com",
    "/blog/", ".blog/", "blog.", "tumblr.com"
]

def is_blog(url):
    return any(p in url.lower() for p in BLOG_PATTERNS)


# ====== BERSIHKAN HTML ======
def clean_html(html):
    clean = re.sub('<.*?>', '', html)
    clean = clean.replace("&nbsp;", " ").strip()
    return clean


# ====== FETCH GOOGLE NEWS GLOBAL ======
def fetch_news(keyword):
    q = quote_plus(keyword)
    url = f"https://news.google.com/rss/search?q={q}&hl=en&gl=US&ceid=US:en"
    return feedparser.parse(url)


# ====== MENGECEK HISTORY UNTUK MENGHINDARI DUPLIKAT ======
def load_history():
    if not os.path.exists("data/news_history.json"):
        return []
    with open("data/news_history.json", "r", encoding="utf-8") as f:
        return json.load(f)

def save_to_history(article):
    os.makedirs("data", exist_ok=True)
    history = load_history()
    history.append(article["link"])
    with open("data/news_history.json", "w", encoding="utf-8") as f:
        json.dump(history, f, indent=4)


# ====== CARI ARTIKEL SESUAI BATAS WAKTU ======
def search_by_time(keywords, max_age_days):

    now = datetime.utcnow()
    limit = now - timedelta(days=max_age_days)
    history = load_history()

    for keyword in keywords:
        feed = fetch_news(keyword)

        for entry in feed.entries:

            if "published_parsed" not in entry:
                continue

            pub = datetime(*entry.published_parsed[:6])

            # Usia artikel
            if pub < limit:
                continue

            link = entry.link

            # Hindari blog
            if is_blog(link):
                continue

            # Hindari artikel yang sudah pernah dipakai
            if link in history:
                continue

            summary = clean_html(entry.summary) if "summary" in entry else ""

            return {
                "keyword": keyword,
                "title": clean_html(entry.title),
                "link": link,
                "summary": summary,
                "published": pub.isoformat()
            }

    return None


# ====== FALLBACK TANPA BATAS USIA ======
def search_oldest_relevant(keywords):

    history = load_history()

    for keyword in keywords:
        feed = fetch_news(keyword)

        for entry in feed.entries:

            link = entry.link

            if is_blog(link):
                continue
            if link in history:
                continue

            summary = clean_html(entry.summary) if "summary" in entry else ""

            pub = None
            if "published_parsed" in entry:
                pub = datetime(*entry.published_parsed[:6]).isoformat()

            return {
                "keyword": keyword,
                "title": clean_html(entry.title),
                "link": link,
                "summary": summary,
                "published": pub or "unknown"
            }

    return None


# ====== MAIN ======
if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument("--keywords-file", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()

    # Load keyword list
    with open(args.keywords_file, "r", encoding="utf-8") as f:
        keywords = [k.strip() for k in f.readlines() if k.strip()]

    # 24 jam
    result = search_by_time(keywords, 1)
    if result:
        print("=== FOUND (24 HOURS) ===")
        save_to_history(result)
        json.dump(result, open(args.out, "w", encoding="utf-8"), indent=4)
        exit()

    # 7 hari
    print("=== NO 24 HOUR NEWS → TRY 7 DAYS ===")
    result = search_by_time(keywords, 7)
    if result:
        print("=== FOUND (7 DAYS) ===")
        save_to_history(result)
        json.dump(result, open(args.out, "w", encoding="utf-8"), indent=4)
        exit()

    # 30 hari
    print("=== NO 7 DAY NEWS → TRY 30 DAYS ===")
    result = search_by_time(keywords, 30)
    if result:
        print("=== FOUND (30 DAYS) ===")
        save_to_history(result)
        json.dump(result, open(args.out, "w", encoding="utf-8"), indent=4)
        exit()

    # fallback
    print("=== NO RECENT NEWS → TRY OLDEST RELEVANT ===")
    result = search_oldest_relevant(keywords)
    if result:
        print("=== USING OLDEST RELEVANT MATCH ===")
        save_to_history(result)
        json.dump(result, open(args.out, "w", encoding="utf-8"), indent=4)
        exit()

    print("=== ABSOLUTELY NO ARTICLE FOUND (VERY RARE) ===")
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump({"error": "no_article_found"}, f, indent=4)
