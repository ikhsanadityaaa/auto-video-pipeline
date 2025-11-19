import feedparser
import argparse
import json
from datetime import datetime, timedelta
from urllib.parse import quote_plus
import re

# ====== TRUSTED NEWS SOURCES ======
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
    "bloomberg.com",
]

# ====== CHECK TRUSTED DOMAIN ======
def is_trusted(url):
    return any(src in url for src in TRUSTED_SOURCES)

# ====== STRIP HTML ======
def clean_html(html):
    clean = re.sub('<.*?>', '', html)
    clean = clean.replace("&nbsp;", " ").strip()
    return clean

# ====== FETCH GOOGLE NEWS (ENGLISH GLOBAL) ======
def fetch_global_news(keyword):
    q = quote_plus(keyword)
    url = f"https://news.google.com/rss/search?q={q}&hl=en&gl=US&ceid=US:en"
    return feedparser.parse(url)

# ====== FIND NEWS (LAST 24 HOURS + TRUSTED SOURCE) ======
def find_recent_news(keywords):

    now = datetime.utcnow()
    limit = now - timedelta(days=1)

    for keyword in keywords:
        feed = fetch_global_news(keyword)

        for entry in feed.entries:

            # Skip if no timestamp
            if "published_parsed" not in entry:
                continue

            pub = datetime(*entry.published_parsed[:6])
            if pub < limit:
                continue

            link = entry.link

            # Filter only trusted sources
            if not is_trusted(link):
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


# ====== MAIN ======
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--keywords-file", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()

    # Load keywords
    with open(args.keywords_file, "r", encoding="utf-8") as f:
        keywords = [k.strip() for k in f.readlines() if k.strip()]

    result = find_recent_news(keywords)

    if result:
        print("=== INTERNATIONAL NEWS FOUND ===")
        print("Keyword :", result["keyword"])
        print("Title   :", result["title"])
        print("Link    :", result["link"])
        print("Summary :", result["summary"])

        with open(args.out, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=4, ensure_ascii=False)
    else:
        print("=== NO TRUSTED INTERNATIONAL NEWS IN LAST 24 HOURS ===")
        with open(args.out, "w", encoding="utf-8") as f:
            json.dump({"error": "no_news"}, f, indent=4)
