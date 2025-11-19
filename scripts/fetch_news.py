import feedparser
import argparse
import json
from datetime import datetime, timedelta
from urllib.parse import quote_plus
import os
import re

# ============================================================
#   GOOGLE NEWS REDIRECT → RAW URL EXTRACTOR (FINAL VERSION)
# ============================================================

def extract_real_url(google_news_url):
    """
    Mengubah Google News redirect URL menjadi URL asli artikel.
    Contoh:
    https://news.google.com/rss/articles/CBMiXWh0dHBzOi8vd3d3LmJiYy5jb20vbmV3cy93b3JsZC1uZXdzLTY3MTE0ODA00gEA
    → https://www.bbc.com/news/world-news-67114800
    """

    # 1. Ambil bagian setelah "/articles/"
    m = re.search(r"/articles/(.*)", google_news_url)
    if not m:
        return google_news_url

    encoded_part = m.group(1)

    # 2. Google News base64 yang sudah dimodifikasi biasanya:
    #    - mengganti '-' → '+'
    #    - mengganti '_' → '/'
    #    - memotong padding "="
    encoded_part = encoded_part.replace("-", "+").replace("_", "/")

    # Tambahkan padding agar panjangnya kelipatan 4
    while len(encoded_part) % 4 != 0:
        encoded_part += "="

    import base64
    try:
        decoded = base64.b64decode(encoded_part).decode("utf-8", errors="ignore")
    except:
        return google_news_url

    # 3. Cari URL asli di dalam hasil decode
    m2 = re.search(r"(https?://[^\s]+)", decoded)
    if m2:
        return m2.group(1)

    return google_news_url


# ============================================================
#   DETEKSI BLOG / NON-CREDIBLE SOURCES
# ============================================================

BAD_DOMAINS = [
    "blogspot", "wordpress", "medium.com", "substack",
    "tumblr", "blog.", ".blog", "localnews", "pressrelease",
    "prnews", "aboutads", "advert", "/sponsored", "tribunnews",
]

def is_allowed_source(url):
    low = url.lower()
    return not any(bad in low for bad in BAD_DOMAINS)


# ============================================================
#   LOAD & SAVE HISTORY (AGAR BERITA TIDAK TERULANG)
# ============================================================

HISTORY_FILE = "data/news_history.json"

def load_history():
    if not os.path.exists(HISTORY_FILE):
        return []

    try:
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return []

def save_history(url):
    old = load_history()
    old.append(url)
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(old, f, indent=4)


def already_used(url):
    return url in load_history()


# ============================================================
#   FETCH GLOBAL GOOGLE NEWS
# ============================================================

def fetch(keyword):
    q = quote_plus(keyword)
    url = f"https://news.google.com/rss/search?q={q}&hl=en&gl=US&ceid=US:en"
    return feedparser.parse(url)


# ============================================================
#   BERSIHKAN HTML RINGKASAN
# ============================================================

def clean_html(html):
    html = re.sub("<.*?>", "", html)
    return html.replace("&nbsp;", " ").strip()


# ============================================================
#   SEARCH NEWS WITH TIME RANGE
# ============================================================

def search_time_range(keywords, days):
    now = datetime.utcnow()
    limit = now - timedelta(days=days)

    for kw in keywords:
        feed = fetch(kw)
        for entry in feed.entries:

            if "published_parsed" not in entry:
                continue

            pub = datetime(*entry.published_parsed[:6])
            if pub < limit:
                continue

            url = extract_real_url(entry.link)

            if not is_allowed_source(url):
                continue

            if already_used(url):
                continue

            return {
                "keyword": kw,
                "title": clean_html(entry.title),
                "summary": clean_html(entry.summary) if "summary" in entry else "",
                "link": url,
                "published": pub.isoformat()
            }

    return None


# ============================================================
#   FALLBACK: AMBIL ARTIKEL PALING RELEVAN (TANPA LIMIT WAKTU)
# ============================================================

def fallback_anytime(keywords):
    for kw in keywords:
        feed = fetch(kw)
        for entry in feed.entries:

            url = extract_real_url(entry.link)

            if not is_allowed_source(url):
                continue

            if already_used(url):
                continue

            return {
                "keyword": kw,
                "title": clean_html(entry.title),
                "summary": clean_html(entry.summary) if "summary" in entry else "",
                "link": url,
            }

    return None


# ============================================================
#   MAIN PROGRAM
# ============================================================

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--keywords-file", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()

    with open(args.keywords_file, "r", encoding="utf-8") as f:
        keywords = [x.strip() for x in f.readlines() if x.strip()]

    # 1. CARI 24 JAM
    result = search_time_range(keywords, 1)
    if result:
        print("=== FOUND RECENT NEWS (1 DAY) ===")
    else:
        print("=== NO 24-HOUR NEWS → TRY 7 DAYS ===")
        result = search_time_range(keywords, 7)

    # 2. CARI 7 HARI
    if not result:
        print("=== NO 7-DAY NEWS → TRY 30 DAYS ===")
        result = search_time_range(keywords, 30)

    # 3. CARI TANPA BATAS WAKTU
    if not result:
        print("=== NO 30-DAY NEWS → ANYTIME SEARCH ===")
        result = fallback_anytime(keywords)

    # 4. TETAP TIDAK ADA
    if not result:
        print("=== ABSOLUTELY NO NEWS FOUND ===")
        with open(args.out, "w", encoding="utf-8") as f:
            json.dump({"error": "no_news"}, f, indent=4)
        exit(0)

    # Simpan hasil
    save_history(result["link"])

    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=4, ensure_ascii=False)

    print("=== NEWS SELECTED ===")
    print("Keyword :", result["keyword"])
    print("Judul   :", result["title"])
    print("Link    :", result["link"])
    print("Published :", result.get("published", "N/A"))
    print("Ringkasan :", result["summary"])
