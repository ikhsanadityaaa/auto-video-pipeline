import feedparser
import argparse
import json
import os
import re
from urllib.parse import quote_plus, unquote, parse_qs
from datetime import datetime, timedelta

# ========== SETTINGS ==========
HISTORY_FILE = "data/news_history.json"
BLOCKED_DOMAINS = [
    "blogspot", "wordpress", "medium.com", "substack",
    "tumblr", "facebook.com", "instagram.com", "pinterest.com",
    "x.com", "twitter.com", "reddit.com", "quora.com",
    "/blog/", "/opinion/"
]

# ========== UTILS ==========
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
    # Coba ambil dari parameter url=
    if "url=" in google_url:
        try:
            qs = parse_qs(google_url.split("?", 1)[1])
            if "url" in qs:
                return unquote(qs["url"][0])
        except:
            pass
    # Jika tidak ada, kembalikan apa adanya
    return google_url

def fetch_google_news(keyword, days=1):
    q = quote_plus(keyword)
    url = f"https://news.google.com/rss/search?q={q}&hl=en&gl=US&ceid=US:en"
    feed = feedparser.parse(url)
    now = datetime.utcnow()
    cutoff = now - timedelta(days=days)
    valid_entries = []
    for e in feed.entries:
        if "published_parsed" not in e:
            continue
        pub = datetime(*e.published_parsed[:6])
        if pub >= cutoff:
            valid_entries.append(e)
    return valid_entries

# ========== MAIN LOGIC ==========
def find_one_relevant_article(keywords):
    history = load_history()
    windows = [1, 7, 30, 365]  # hari
    for days in windows:
        print(f"=== MENCARI BERITA {days}-HARI TERAKHIR ===")
        for kw in keywords:
            entries = fetch_google_news(kw, days)
            for e in entries:
                real_link = extract_real_url(e.link)
                if is_blocked(real_link):
                    continue
                if real_link in history:
                    continue
                return {
                    "keyword": kw,
                    "title": clean_html(e.title),
                    "link": real_link,
                    "summary": clean_html(e.summary) if hasattr(e, "summary") else "",
                    "published": datetime(*e.published_parsed[:6]).isoformat()
                }
    return None

# ========== MAIN ==========
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--keywords-file", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()

    with open(args.keywords_file, "r", encoding="utf-8") as f:
        keywords = [k.strip() for k in f if k.strip()]

    article = find_one_relevant_article(keywords)

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
        print("❌ TIDAK ADA BERITA DITEMUKAN")
        with open(args.out, "w", encoding="utf-8") as f:
            json.dump({"error": "no_news"}, f, indent=2)
