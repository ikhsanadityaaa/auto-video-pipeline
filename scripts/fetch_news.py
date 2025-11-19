import feedparser
import argparse
import json
import os
import re
from urllib.parse import quote_plus
from datetime import datetime, timedelta

# Lokasi penyimpanan history
HISTORY_FILE = "data/news_history.json"

# Domain yang dianggap blog atau tidak layak
BLOCKED_DOMAINS = [
    "blogspot", "wordpress", "medium.com", "substack",
    "tumblr", "reddit", "quora", "blog.", "/blog",
]

# ==================================================
# CLEAN GOOGLE NEWS REDIRECT → JADI LINK ASLI
# ==================================================
def clean_google_news_url(url):
    if "url=" in url:
        real = url.split("url=")[-1]
        real = real.split("&")[0]
        return real
    return url


# ==================================================
# LOAD / SAVE HISTORY (untuk cegah artikel duplikat)
# ==================================================
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
        json.dump(history, f, indent=4)


# ==================================================
# Bersihkan HTML ringkasan
# ==================================================
def clean_html(text):
    if not text:
        return ""
    text = re.sub("<.*?>", "", text)
    return text.replace("&nbsp;", " ").strip()


# ==================================================
# Cek apakah website termasuk blog
# ==================================================
def is_blocked(url):
    url = url.lower()
    return any(b in url for b in BLOCKED_DOMAINS)


# ==================================================
# Fetch Google News RSS global
# ==================================================
def fetch_feed(keyword):
    q = quote_plus(keyword)      # FIX URL ERROR
    url = f"https://news.google.com/rss/search?q={q}&hl=en&gl=US&ceid=US:en"
    return feedparser.parse(url)


# ==================================================
# Cari berita berdasarkan batas hari
# ==================================================
def search_news(keywords, days, max_articles=5):
    now = datetime.utcnow()
    min_date = now - timedelta(days=days)

    history = load_history()
    found = []

    for keyword in keywords:
        feed = fetch_feed(keyword)

        for entry in feed.entries:
            if "published_parsed" not in entry:
                continue

            published = datetime(*entry.published_parsed[:6])
            if published < min_date:
                continue

            # Clean data
            link = clean_google_news_url(entry.link)
            title = clean_html(entry.title)
            summary = clean_html(entry.summary) if hasattr(entry, "summary") else ""

            # Skip blog
            if is_blocked(link):
                continue

            # Skip duplicate from history
            if link in history:
                continue

            found.append({
                "keyword": keyword,
                "title": title,
                "link": link,
                "summary": summary,
                "published": published.isoformat()
            })

            if len(found) >= max_articles:
                return found

    return found


# ==================================================
# MAIN EXECUTION
# ==================================================
if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument("--keywords-file", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()

    # Muat keyword
    with open(args.keywords_file, "r", encoding="utf-8") as f:
        keywords = [x.strip() for x in f.readlines() if x.strip()]

    # 1 hari
    articles = search_news(keywords, 1)

    if not articles:
        print("=== NO 24 HOUR NEWS → TRY 7 DAYS ===")
        articles = search_news(keywords, 7)

    if not articles:
        print("=== NO 7 DAY NEWS → TRY 30 DAYS ===")
        articles = search_news(keywords, 30)

    if not articles:
        print("=== NO 30 DAY NEWS → TRY 90 DAYS ===")
        articles = search_news(keywords, 90)

    # Jika tetap tidak ada → selesai dengan error
    if not articles:
        print("=== NO NEWS FOUND AT ALL ===")
        with open(args.out, "w", encoding="utf-8") as f:
            json.dump({"error": "no_news"}, f, indent=4)
        exit(0)

    # Simpan ke output
    print(f"=== OK | FOUND {len(articles)} ARTICLES ===")
    for art in articles:
        print(f"- {art['title']}")
        print(f"  {art['link']}")

    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(articles, f, indent=4, ensure_ascii=False)

    # Tambahkan ke history
    history = load_history()
    for art in articles:
        history.append(art["link"])
    save_history(history)
