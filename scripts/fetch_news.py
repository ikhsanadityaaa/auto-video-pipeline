import feedparser
import argparse
import json
from datetime import datetime, timedelta
from urllib.parse import quote_plus, unquote, urlparse, parse_qs
import re
import os

# ========== DOMAIN YANG AKAN DI-SKIP (BLOG / SPAM / OPINI) ==========
SKIP_DOMAINS = [
    "blogspot", "wordpress", "medium.com", "substack",
    "quora.com", "theconversation", "yahoo.com/news/opinion",
    "/opinion/", "/opinions/"
]

# ========== RIWAYAT ARTIKEL YANG SUDAH DIPAKAI ==========
HISTORY_FILE = "data/news_history.json"

def load_history():
    if not os.path.exists(HISTORY_FILE):
        return set()

    try:
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            return set(data)
    except:
        return set()

def save_history(history):
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(list(history), f, indent=4)

# ========== CLEAN HTML ==========
def clean_html(html):
    clean = re.sub('<.*?>', '', html)
    clean = clean.replace("&nbsp;", " ").strip()
    return clean

# ========== CEK DOMEN BLOG / SPAM ==========
def is_bad_source(url):
    return any(x.lower() in url.lower() for x in SKIP_DOMAINS)

# ========== GOOGLE REDIRECT → URL ASLI ==========
def extract_real_url(google_url):
    try:
        parsed = urlparse(google_url)
        qs = parse_qs(parsed.query)

        # Jika Google menyertakan parameter url=
        if "url" in qs:
            return qs["url"][0]

        # Pola redirect lain (Google kadang encode dalam "ved=" atau truncated)
        if google_url.startswith("https://news.google.com/rss/articles/"):
            # Google biasanya encode URL di bagian setelah artikelnya
            decoded = unquote(google_url)
            match = re.search(r"(https?://[^\s]+)", decoded)
            if match:
                url = match.group(1)
                if "google.com" not in url:
                    return url

        return google_url
    except:
        return google_url

# ========== FETCH GLOBAL NEWS ==========
def fetch_global_news(keyword):
    q = quote_plus(keyword)
    url = f"https://news.google.com/rss/search?q={q}&hl=en&gl=US&ceid=US:en"
    return feedparser.parse(url)

# ========== SEARCH FUNCTION ==========
def search_news(keywords, day_range):
    history = load_history()
    now = datetime.utcnow()
    limit = now - timedelta(days=day_range)
    collected = []

    for keyword in keywords:
        feed = fetch_global_news(keyword)

        for entry in feed.entries:
            # Filter waktu
            if "published_parsed" not in entry:
                continue

            pub = datetime(*entry.published_parsed[:6])
            if pub < limit:
                continue

            # Ambil link asli
            link = extract_real_url(entry.link)

            # Skip domain sampah
            if is_bad_source(link):
                continue

            # Skip artikel yang pernah dipakai
            if link in history:
                continue

            # Clean summary
            summary = clean_html(entry.summary) if "summary" in entry else ""

            collected.append({
                "keyword": keyword,
                "title": clean_html(entry.title),
                "link": link,
                "summary": summary,
                "published": pub.isoformat()
            })

    return collected

# ========== MAIN EXECUTION ==========
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--keywords-file", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()

    # Load keywords
    with open(args.keywords_file, "r", encoding="utf-8") as f:
        keywords = [k.strip() for k in f.readlines() if k.strip()]

    result = None

    # Cari 24 jam
    articles = search_news(keywords, 1)
    if articles:
        print("=== OK | FOUND RECENT ARTICLES ===")
        result = articles
    else:
        print("=== NO 24 HOUR NEWS → TRY 3 DAYS ===")
        articles = search_news(keywords, 3)

    if not articles:
        print("=== NO 3 DAY NEWS → TRY 7 DAYS ===")
        articles = search_news(keywords, 7)

    if not articles:
        print("=== NO 7 DAY NEWS → TRY 30 DAYS ===")
        articles = search_news(keywords, 30)

    if not articles:
        print("=== NO NEWS FOUND AT ALL ===")
        with open(args.out, "w", encoding="utf-8") as f:
            json.dump({"error": "no_news"}, f, indent=4)
        exit()

    # Simpan history untuk cegah duplikasi
    history = load_history()
    for item in articles:
        history.add(item["link"])
    save_history(history)

    # Tampilkan hasil
    print(f"=== OK | FOUND {len(articles)} ARTICLES ===")
    for a in articles:
        print("-", a["title"], "|", a["link"])

    # Simpan JSON output
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(articles, f, indent=4, ensure_ascii=False)
