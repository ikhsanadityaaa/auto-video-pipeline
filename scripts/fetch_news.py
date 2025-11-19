import feedparser
import argparse
import json
from datetime import datetime, timedelta
from urllib.parse import quote_plus
import re

# ====== FINAL TRUSTED SOURCES FOR YOUR NICHE ======
TRUSTED_SOURCES = [
    "bbc.com",
    "cnn.com",
    "reuters.com",
    "apnews.com",
    "nytimes.com",
    "nationalgeographic.com",
    "theguardian.com",
    "aljazeera.com",
    "abcnews.go.com",
    "nbcnews.com",
    "smithsonianmag.com",
    "nature.com",
    "livescience.com",
    "history.com",
    "sky.com",
    "sciencealert.com",
    "scientificamerican.com",
    "space.com",
    "wired.com",
    "discovery.com",
    "bloomberg.com"
]

def is_trusted(url):
    return any(src in url for src in TRUSTED_SOURCES)

def clean_html(html):
    clean = re.sub('<.*?>', '', html)
    clean = clean.replace("&nbsp;", " ").strip()
    return clean

def fetch_global_news(keyword):
    q = quote_plus(keyword)
    url = f"https://news.google.com/rss/search?q={q}&hl=en&gl=US&ceid=US:en"
    return feedparser.parse(url)

def search_news(keywords, days):
    limit = datetime.utcnow() - timedelta(days=days)
    best_result = None

    for keyword in keywords:
        feed = fetch_global_news(keyword)

        for entry in feed.entries:
            if "published_parsed" not in entry:
                continue

            pub = datetime(*entry.published_parsed[:6])

            link = entry.link

            if not is_trusted(link):
                continue

            summary = clean_html(entry.summary) if "summary" in entry else ""

            # Jika masih dalam range waktu → langsung return
            if pub >= limit:
                return {
                    "keyword": keyword,
                    "title": clean_html(entry.title),
                    "link": link,
                    "summary": summary,
                    "published": pub.isoformat()
                }

            # Jika mencari fallback → simpan artikel paling relevan
            if best_result is None:
                best_result = {
                    "keyword": keyword,
                    "title": clean_html(entry.title),
                    "link": link,
                    "summary": summary,
                    "published": pub.isoformat()
                }

    return best_result


# ====== MAIN ======
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--keywords-file", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()

    with open(args.keywords_file, "r", encoding="utf-8") as f:
        keywords = [k.strip() for k in f if k.strip()]

    # 1. Cari 24 jam
    result = search_news(keywords, 1)

    if result:
        print("=== NEWS FOUND (LAST 24 HOURS) ===")
    else:
        print("=== NO 24 HOUR NEWS → TRY 7 DAYS ===")
        result = search_news(keywords, 7)

    if not result:
        print("=== NO 7 DAY NEWS → TRY 30 DAYS ===")
        result = search_news(keywords, 30)

    if not result:
        print("=== NO 30 DAY NEWS → USING OLDEST RELEVANT ARTICLE ===")
        result = search_news(keywords, 9999)

    if not result:
        print("=== ABSOLUTELY NO NEWS FOUND ===")
        with open(args.out, "w", encoding="utf-8") as f:
            json.dump({"error": "no_news"}, f, indent=4)
        exit(0)

    print("Keyword :", result["keyword"])
    print("Title   :", result["title"])
    print("Link    :", result["link"])
    print("Summary :", result["summary"])
    print("Date    :", result["published"])

    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=4, ensure_ascii=False)
