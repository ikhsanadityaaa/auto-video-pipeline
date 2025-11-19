import feedparser
import argparse
import json
from datetime import datetime, timedelta
from urllib.parse import quote_plus
import re

# ====== DOMAIN YANG DINILAI KREDIBEL ======
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
    "bloomberg.com",  # DITAMBAHKAN
]

# ====== CEK APAKAH DOMAIN KREDIBEL ======
def is_trusted(url):
    return any(src in url for src in TRUSTED_SOURCES)

# ====== CLEAN HTML ======
def clean_html(html):
    clean = re.sub('<.*?>', '', html)
    clean = clean.replace("&nbsp;", " ").strip()
    return clean

# ====== FETCH GOOGLE NEWS GLOBAL ======
def fetch_global_news(keyword):
    q = quote_plus(keyword)
    url = f"https://news.google.com/rss/search?q={q}&hl=en&gl=US&ceid=US:en"
    return feedparser.parse(url)


# ====== CARI BERITA 24 JAM TERAKHIR DARI SUMBER KREDIBEL ======
def find_recent_news(keywords):

    now = datetime.utcnow()
    limit = now - timedelta(days=1)

    for keyword in keywords:
        feed = fetch_global_news(keyword)

        for entry in feed.entries:
            if "published_parsed" not in entry:
                continue

            pub = datetime(*entry.published_parsed[:6])
            if pub < limit:
                continue  # skip artikel lama

            link = entry.link

            # Hanya ambil sumber kredibel
            if not is_trusted(link):
                continue

            # Clean ringkasan
            summary = clean_html(entry.summary) if "summary" in entry else ""

            return {
                "keyword": keyword,
                "title": clean_html(entry.title),
                "link": link,
                "summary": summary,
                "published": pub.isoformat()
            }

    return None


# ====== MAIN PROGRAM ======
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
        print("=== BERITA INTERNASIONAL DITEMUKAN ===")
        print("Keyword :", result["keyword"])
        print("Judul   :", result["title"])
        print("Link    :", result["link"])
        print("Ringkas :", result["summary"])

        with open(args.out, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=4, ensure_ascii=False)
    else:
        print("=== TIDAK ADA BERITA 24 JAM TERAKHIR YANG KREDIBEL ===")
        with open(args.out, "w", encoding="utf-8") as f:
            json.dump({"error": "no_news"}, f, indent=4)
