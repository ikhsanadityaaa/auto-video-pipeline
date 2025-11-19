# scripts/fetch_news.py
# Versi final sesuai instruksi user:
# - keywords bahasa Inggris (tetap simpan "mendadak kaya")
# - cari internasional via Google News RSS
# - prioritas TRUSTED_SOURCES
# - window: 24h -> 7d -> 30d -> any (oldest relevant)
# - jika tidak ada di TRUSTED_SOURCES, boleh cari di OTHER_SOURCES (bukan blog)
# - skip domain yang terdeteksi blog (medium, blogspot, wordpress, dll)
# Cara pakai:
# python scripts/fetch_news.py --keywords-file config/keywords.txt --out topic.json

import feedparser
import argparse
import json
from datetime import datetime, timedelta
from urllib.parse import quote_plus, urlparse
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
    "bloomberg.com",          # ditambahkan
    "washingtonpost.com",
    "wsj.com",
    "economist.com",
    "pbs.org",
]

# ====== SUMBER LAIN YANG BOLEH DIPAKAI JIKA TRUSTED KOSONG (BUKAN BLOG) ======
OTHER_SOURCES = [
    "yahoo.com",
    "yahoo.co.uk",
    "rawstory.com",
    "forbes.com",
    "vice.com",
    "time.com",
    "vox.com",
    "bbc.co.uk",
    "independent.co.uk",
    "sciencedaily.com",
    "newscientist.com",
    "foreignpolicy.com",
    "cnbc.com",
    "barrons.com",
]

# ====== DOMAIN YANG DIANGGAP 'BLOG' DAN HARUS DIHINDARI ======
BLOG_INDICATORS = [
    "medium.com",
    "blogspot.com",
    "wordpress.com",
    "blog",
    "substack.com",
]

# ====== BANTUAN: CEK APAKAH DOMAIN KREDIBEL ======
def domain_of(url):
    try:
        parsed = urlparse(url)
        host = parsed.netloc.lower()
        # hilangkan port jika ada
        if ":" in host:
            host = host.split(":")[0]
        return host
    except Exception:
        return url.lower()

def is_trusted(url):
    host = domain_of(url)
    return any(src in host for src in TRUSTED_SOURCES)

def is_other_source(url):
    host = domain_of(url)
    return any(src in host for src in OTHER_SOURCES)

def is_blog_like(url):
    host = domain_of(url)
    # cek indicator pada host atau path
    if any(ind in host for ind in BLOG_INDICATORS):
        return True
    # juga cek jika path mengandung '/blog' atau '/author'
    try:
        p = urlparse(url)
        if "/blog" in p.path.lower() or "/author" in p.path.lower():
            return True
    except Exception:
        pass
    return False

# ====== CLEAN HTML ======
def clean_html(html):
    if not html:
        return ""
    clean = re.sub('<.*?>', '', html)
    clean = clean.replace("&nbsp;", " ").strip()
    return clean

# ====== FETCH GOOGLE NEWS GLOBAL ======
def fetch_global_news(keyword):
    # keyword sudah diasumsikan berebahasa Inggris
    q = quote_plus(keyword)
    url = f"https://news.google.com/rss/search?q={q}&hl=en&gl=US&ceid=US:en"
    return feedparser.parse(url)

# ====== FIND ENTRY SESUAI KEBIJAKAN ======
def choose_entry(entries, earliest_allowed, prefer_trusted=True):
    """
    entries: list feed.entries
    earliest_allowed: datetime object
    prefer_trusted: kalau True cari dulu trusted, jika False cari dari semua non-blog source
    """
    # pertama cek trusted (jika prefer_trusted True)
    if prefer_trusted:
        for e in entries:
            if "published_parsed" not in e:
                continue
            pub = datetime(*e.published_parsed[:6])
            if pub < earliest_allowed:
                continue
            link = e.get("link", "")
            if is_trusted(link) and not is_blog_like(link):
                return e
    # kalau belum ditemukan atau prefer_trusted False, cari other sources yang bukan blog
    for e in entries:
        if "published_parsed" not in e:
            continue
        pub = datetime(*e.published_parsed[:6])
        if pub < earliest_allowed:
            continue
        link = e.get("link", "")
        if not is_blog_like(link):
            # kalau trusted, oke. kalau other, cek is_other_source or generic
            if is_trusted(link) or is_other_source(link) or True:
                return e
    return None

# ====== LOGIKA UTAMA: PERLUAS WINDOW JIKA TIDAK ADA ======
def find_recent_news(keywords):
    now = datetime.utcnow()

    # windows: 1 day, 7 days, 30 days, none (ambil oldest relevant)
    windows = [
        ("24 hours", now - timedelta(days=1)),
        ("7 days", now - timedelta(days=7)),
        ("30 days", now - timedelta(days=30)),
        ("any", datetime.min)
    ]

    # dua fase: fase 1 coba TRUSTED_SOURCES
    for label, earliest in windows:
        print(f"=== TRYING WINDOW: {label} (since {earliest.isoformat()}) ===")
        for kw in keywords:
            feed = fetch_global_news(kw)
            entry = choose_entry(feed.entries, earliest, prefer_trusted=True)
            if entry:
                return build_result_from_entry(kw, entry)
    # fase 2: jika tidak ada trusted sama sekali, boleh coba sumber lain non-blog
    for label, earliest in windows:
        print(f"=== NO TRUSTED → TRY OTHER SOURCES WINDOW: {label} ===")
        for kw in keywords:
            feed = fetch_global_news(kw)
            entry = choose_entry(feed.entries, earliest, prefer_trusted=False)
            if entry and not is_blog_like(entry.get("link", "")):
                return build_result_from_entry(kw, entry)

    # jika tetap tidak ada, return None
    return None

def build_result_from_entry(keyword, entry):
    pub = None
    if "published_parsed" in entry:
        pub = datetime(*entry.published_parsed[:6])
    link = entry.get("link", "")
    title = clean_html(entry.get("title", ""))
    summary = clean_html(entry.get("summary", "")) if entry.get("summary") else ""
    host = domain_of(link)
    return {
        "keyword": keyword,
        "title": title,
        "link": link,
        "summary": summary,
        "published": pub.isoformat() if pub else None,
        "source": host
    }

# ====== MAIN PROGRAM ======
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--keywords-file", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()

    # Load keywords (as English phrases). Keep "mendadak kaya" jika ada.
    with open(args.keywords_file, "r", encoding="utf-8") as f:
        keywords = [k.strip() for k in f.readlines() if k.strip()]

    print("=== START SEARCH: keywords count =", len(keywords), "===")
    result = find_recent_news(keywords)

    if result:
        print("=== NEWS FOUND ===")
        print("Keyword :", result["keyword"])
        print("Title   :", result["title"])
        print("Link    :", result["link"])
        print("Source  :", result.get("source"))
        print("Summary :", (result["summary"] or "(no summary)"))
        with open(args.out, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=4, ensure_ascii=False)
    else:
        print("=== ABSOLUTELY NO NEWS FOUND ===")
        # jika tidak ditemukan sama sekali, kita tidak berhenti.
        # tulis file out dengan error untuk pipeline fallback.
        with open(args.out, "w", encoding="utf-8") as f:
            json.dump({"error": "no_news"}, f, indent=4)
