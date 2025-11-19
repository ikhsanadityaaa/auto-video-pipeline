import feedparser
import argparse
import json
import re
from urllib.parse import unquote, urlparse, parse_qs
from datetime import datetime, timedelta
import os

# ========== DOMAIN YANG TIDAK DIPERBOLEHKAN ==========
BLOCKED_DOMAINS = [
    "blogspot", "wordpress", "medium.com", "substack",
    "facebook.com", "instagram.com", "pinterest.com",
    "tiktok.com", "x.com", "twitter.com"
]

# ========== LOAD HISTORY ==========
HISTORY_FILE = "data/news_history.json"

def load_history():
    if not os.path.exists(HISTORY_FILE):
        return []
    try:
        with open(HISTORY_FILE, "r") as f:
            return json.load(f)
    except:
        return []

def save_history(history):
    with open(HISTORY_FILE, "w") as f:
        json.dump(history, f, indent=2)

# ========== DETECT BLOG ==========
def is_blocked(url):
    url = url.lower()
    return any(bad in url for bad in BLOCKED_DOMAINS)

# ========== CLEAN HTML ==========
def clean_html(html):
    html = re.sub('<.*?>', '', html)
    return html.replace("&nbsp;", " ").strip()

# ========== CONVERT GOOGLE NEWS LINK KE LINK ASLI ==========
def extract_real_url(google_url):
    if "url=" in google_url:
        try:
            q = parse_qs(google_url.split("?")[1])
            real = q.get("url")
            if real:
                return unquote(real[0])
        except:
            pass
    # If Google stores link in entry.id and not in link
    return google_url

# ========== FETCH FROM GOOGLE NEWS ==========
def fetch(keyword):
    url = f"https://news.google.com/rss/search?q={keyword}&hl=en&gl=US&ceid=US:en"
    return feedparser.parse(url)

# ========== CORE SEARCH FUNCTION ==========
def search_news(keywords, days_limit, max_articles=5):
    history = load_history()
    now = datetime.utcnow()
    cutoff = now - timedelta(days=days_limit)

    results = []

    for keyword in keywords:
        feed = fetch(keyword)

        for entry in feed.entries:
            if "published_parsed" not in entry:
                continue

            pub = datetime(*entry.published_parsed[:6])
            if pub < cutoff:
                continue

            clean_title = clean_html(entry.title)

            link_source = extract_real_url(entry.link)

            if is_blocked(link_source):
                continue

            if link_source in history:
                continue

            summary = clean_html(entry.summary) if "summary" in entry else ""

            result_item = {
                "keyword": keyword,
                "title": clean_title,
                "link": link_source,
                "summary": summary,
                "published": pub.isoformat()
            }

            results.append(result_item)

            if len(results) >= max_articles:
                return results

    return results

# ========== FALLBACK SEARCH ==========
def fallback_search(keywords):
    feed = fetch(keywords[0])
    results = []
    for entry in feed.entries[:5]:
        link = extract_real_url(entry.link)
        if not is_blocked(link):
            results.append({
                "keyword": keywords[0],
                "title": clean_html(entry.title),
                "link": link,
                "summary": clean_html(entry.summary) if "summary" in entry else "",
                "published": "unknown"
            })
    return results

# ========== MAIN ==========
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--keywords-file", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()

    with open(args.keywords_file, "r") as f:
        keywords = [x.strip() for x in f.readlines() if x.strip()]

    # Try fresh news first
    result = search_news(keywords, 1, max_articles=5)

    if not result:
        print("=== NO 24 HOUR NEWS → TRY 7 DAYS ===")
        result = search_news(keywords, 7, max_articles=5)

    if not result:
        print("=== NO 7 DAY NEWS → TRY 30 DAYS ===")
        result = search_news(keywords, 30, max_articles=5)

    if not result:
        print("=== NO 30 DAY NEWS → FALLBACK SIMPLE ===")
        result = fallback_search(keywords)

    if not result:
        print("=== ABSOLUTELY NO NEWS FOUND ===")
        with open(args.out, "w") as f:
            json.dump({"error": "no_news"}, f)
        exit()

    print(f"=== OK | FOUND {len(result)} ARTICLES ===")
    for r in result:
        print(f"- {r['title']}")
        print(r["link"])

    # Save output
    with open(args.out, "w") as f:
        json.dump(result, f, indent=2)

    # Update history
    history = load_history()
    for r in result:
        if r["link"] not in history:
            history.append(r["link"])
    save_history(history)
