import feedparser
import argparse
import json
import os
import re
from urllib.parse import quote_plus, unquote, parse_qs
from datetime import datetime, timedelta

# === KONFIGURASI ===
HISTORY_FILE = "data/news_history.json"

# Domain/blog yang harus dihindari
BLOCKED_DOMAINS = [
    "blogspot", "wordpress", "medium.com", "substack.com",
    "tumblr.com", "facebook.com", "instagram.com", "pinterest.com",
    "x.com", "twitter.com", "reddit.com", "quora.com",
    "/blog/", "/opinion/", "forum", "pressrelease"
]

# === FUNGSI BANTU ===

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
    """Convert Google News redirect URL to original article URL."""
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

def search_news(keywords, min_days_ago, max_days_ago=0):
    """Cari berita dalam rentang waktu tertentu."""
    now = datetime.utcnow()
    cutoff = now - timedelta(days=min_days_ago)
    history = load_history()
    for keyword in keywords:
        feed = fetch_feed(keyword)
        for entry in feed.entries:
            if "published_parsed" not in entry:
                continue
            pub = datetime(*entry.published_parsed[:6])
            if pub < cutoff:
                continue
            if max_days_ago > 0 and (now - pub).days < max_days_ago:
                continue
            real_link = extract_real_url(entry.link)
            if is_blocked(real_link):
                continue
            if real_link in history:
                continue
            return {
                "keyword": keyword,
                "title": clean_html(entry.title),
                "link": real_link,
                "summary": clean_html(entry.summary) if "summary" in entry else "",
                "published": pub.isoformat()
            }
    return None

# === MAIN ===

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--keywords-file", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()

    with open(args.keywords_file, "r", encoding="utf-8") as f:
        keywords = [k.strip() for k in f if k.strip()]

    # Prioritas: berita 24 jam terakhir
    article = search_news(keywords, min_days_ago=1)

    if not article:
        print("=== Tidak ada berita 24 jam → coba 7 hari terakhir ===")
        article = search_news(keywords, min_days_ago=7)

    if not article:
        print("=== Tidak ada berita 7 hari → coba 30 hari terakhir ===")
        article = search_news(keywords, min_days_ago=30)

    if not article:
        print("=== Tidak ada berita 30 hari → ambil artikel paling relevan (tanpa batas waktu) ===")
        article = search_news(keywords, min_days_ago=3650)  # ~10 tahun

    if article:
        print("✅ BERITA DITEMUKAN")
        print(f"Judul   : {article['title']}")
        print(f"Link    : {article['link']}")
        print(f"Keyword : {article['keyword']}")

        # Simpan ke output
        with open(args.out, "w", encoding="utf-8") as f:
            json.dump(article, f, indent=2, ensure_ascii=False)

        # Update history
        history = load_history()
        history.add(article["link"])
        save_history(history)
    else:
        print("❌ TIDAK ADA BERITA YANG COCOK DITEMUKAN")
        with open(args.out, "w", encoding="utf-8") as f:
            json.dump({"error": "no_news"}, f, indent=2)
