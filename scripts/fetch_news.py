# scripts/fetch_news.py
import feedparser
import json
import sys
from datetime import datetime, timedelta
from urllib.parse import quote_plus
import os

def fetch_google_news(query):
    q = quote_plus(query)
    url = f"https://news.google.com/rss/search?q={q}"
    feed = feedparser.parse(url)
    return feed.entries

def find_recent_news(keywords):
    cutoff = datetime.utcnow() - timedelta(days=1)
    for kw in keywords:
        entries = fetch_google_news(kw)
        for e in entries:
            try:
                if hasattr(e, 'published_parsed') and e.published_parsed:
                    pub = datetime(*e.published_parsed[:6])
                else:
                    pub = datetime.utcnow()
                if pub > cutoff:
                    summary = getattr(e, 'summary', '')
                    yield {
                        "keyword": kw,
                        "title": e.title,
                        "link": e.link,
                        "summary": summary,
                        "published": pub.isoformat()
                    }
            except Exception:
                continue

if __name__ == "__main__":
    kw_file = "config/keywords.txt"
    if len(sys.argv) > 1:
        kw_file = sys.argv[1]
    if not os.path.exists(kw_file):
        kw_file = "config/keywords.txt"
    with open(kw_file, "r", encoding="utf-8") as f:
        kws = [l.strip() for l in f if l.strip()]
    results = list(find_recent_news(kws))
    # If no recent news, fallback to historical fetch by searching again and taking first hits
    if not results:
        for kw in kws:
            entries = fetch_google_news(kw)
            if entries:
                e = entries[0]
                results.append({
                    "keyword": kw,
                    "title": e.title,
                    "link": e.link,
                    "summary": getattr(e, 'summary', ''),
                    "published": datetime.utcnow().isoformat()
                })
    # take top 2 candidates
    out = results[:2] if results else []
    with open("topic.json", "w", encoding="utf-8") as o:
        json.dump(out, o, ensure_ascii=False, indent=2)
    print("Wrote topic.json with", len(out), "items")
