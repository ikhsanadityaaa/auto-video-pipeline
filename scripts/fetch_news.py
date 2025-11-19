import feedparser
import argparse
import json
import os
from datetime import datetime, timedelta
from urllib.parse import quote_plus
import re

# File riwayat berita
HISTORY_FILE = "data/news_history.json"

# Domain yang dianggap blog atau tidak kredibel
BLOCKED_DOMAINS = [
    "blogspot.", "wordpress.", "medium.com", "substack.com",
    "tumblr.com", "blog.", "/tag/", "reddit.com", "quora.com"
]

# Bersihkan HTML
def clean_html(text):
    if not text:
        return ""
    text = re.sub("<.*?>", " ", text)
    return text.replace("&nbsp;", " ").strip()

# Deteksi blog / domain tidak kredibel
def is_blog(url):
    url_low = url.lower()
    return any(b in url_low for b in BLOCKED_DOMAINS)

# Convert Google redirect menjadi link asli
def convert_google_news_url(url):
    if "news.google.com" not in url:
        return url
    if "url=" in url:
        try:
            real = url.split("url=")[1].split("&")[0]
            return real
        except:
            return url
    return url

# Fetch RSS global
def fetch_news(keyword):
    q = quote_plus(keyword)
    urls = [
        f"https://news.google.com/rss/search?q={q}&hl=en&gl=US&ceid=US:en",
        f"https://news.google.com/rss/search?q={q}&hl=id&gl=ID&ceid=ID:id",
        f"https://news.google.com/rss/search?q={q}&hl=en&gl=GB&ceid=GB:en"
    ]
    feeds = []
    for u in urls:
        feeds.extend(feedparser.parse(u).entries)
    return feeds

# Load history
def load_history():
    if not os.path.exists(HISTORY_FILE):
        return []
    try:
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return []

# Save history
def save_history(data):
    os.makedirs("data", exist_ok=True)
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)

# Filter berita berdasarkan waktu
def filter_by_time(entries, days):
    limit = datetime.utcnow() - timedelta(days=days)
    result = []
    for e in entries:
        if "published_parsed" not in e:
            continue
        dt = datetime(*e.published_parsed[:6])
        if dt >= limit:
            result.append(e)
    return result

# Bersihkan dan format artikel
def process_entry(entry):
    link = convert_google_news_url(entry.link)
    if is_blog(link):
        return None

    summary = clean_html(entry.summary) if "summary" in entry else ""

    return {
        "title": clean_html(entry.title),
        "link": link,
        "summary": summary,
        "published": datetime(*entry.published_parsed[:6]).isoformat(),
    }

# Cari artikel berdasarkan tier waktu
def search_articles(keywords):
    history = load_history()
    found = []

    for kw in keywords:
        entries = fetch_news(kw)

        # 1. berita 24 jam
        recent = filter_by_time(entries, 1)
        for e in recent:
            art = process_entry(e)
            if art and art["link"] not in history:
                art["keyword"] = kw
                found.append(art)

        if found:
            return found[:3]  # ambil max 3 artikel

        # 2. berita 7 hari
        recent = filter_by_time(entries, 7)
        for e in recent:
            art = process_entry(e)
            if art and art["link"] not in history:
                art["keyword"] = kw
                found.append(art)

        if found:
            return found[:3]

        # 3. berita 30 hari
        recent = filter_by_time(entries, 30)
        for e in recent:
            art = process_entry(e)
            if art and art["link"] not in history:
                art["keyword"] = kw
                found.append(art)

        if found:
            return found[:3]

        # 4. ambil artikel paling relevan
        for e in entries:
            art = process_entry(e)
            if art and art["link"] not in history:
                art["keyword"] = kw
                found.append(art)
                break

        if found:
            return found[:3]

    return []

# MAIN
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--keywords-file", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()

    # load keywords
    with open(args.keywords_file, "r", encoding="utf-8") as f:
        keywords = [k.strip() for k in f.readlines() if k.strip()]

    articles = search_articles(keywords)

    if not articles:
        print("=== NO NEWS FOUND AT ALL ===")
        with open(args.out, "w", encoding="utf-8") as f:
            json.dump({"error": "no_news"}, f, indent=4)
        exit(0)

    # simpan hasil
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(articles, f, indent=4, ensure_ascii=False)

    # update history
    history = load_history()
    for a in articles:
        history.append(a["link"])
    save_history(history)

    print(f"=== OK | FOUND {len(articles)} ARTICLES ===")
    for a in articles:
        print(f"- {a['title']}")
