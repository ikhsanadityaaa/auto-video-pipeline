import feedparser
from urllib.parse import quote_plus

# Daftar kata kunci global
KEYWORDS = [
    "misteri dunia",
    "konspirasi",
    "penelitian aneh",
    "percobaan aneh",
    "fenomena aneh",
    "kisah tragis",
    "misteri yang belum terpecahkan",
    "time travel",
    "kejadian bersejarah yang mengubah dunia"
]

def fetch_google_news(keyword):
    """Ambil berita dari Google News RSS (global)"""
    q = quote_plus(keyword)  # MENCEGAH ERROR SPACE
    url = f"https://news.google.com/rss/search?q={q}&hl=id&gl=ID&ceid=ID:id"
    return feedparser.parse(url)

def find_recent_news():
    """Ambil satu berita terbaru dari semua keyword."""
    for keyword in KEYWORDS:
        feed = fetch_google_news(keyword)
        if not feed.entries:
            continue
        # Ambil berita pertama
        e = feed.entries[0]
        return {
            "keyword": keyword,
            "title": e.title,
            "link": e.link,
            "summary": e.summary if "summary" in e else "",
        }
    return None

if __name__ == "__main__":
    result = find_recent_news()
    if result:
        print("=== BERITA DITEMUKAN ===")
        print("Keyword :", result["keyword"])
        print("Judul   :", result["title"])
        print("Link    :", result["link"])
        print("Ringkas :", result["summary"])
    else:
        print("Tidak ada berita ditemukan.")
