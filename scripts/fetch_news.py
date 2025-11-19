import feedparser
import json
from datetime import datetime, timedelta

# daftar kategori yang ingin kita cari
CATEGORIES = [
    "berita misteri",
    "peristiwa aneh",
    "tragedi",
    "penemuan sains",
    "arkeologi",
    "sejarah Indonesia",
]

def fetch_google_news(keyword):
    url = f"https://news.google.com/rss/search?q={keyword}&hl=id&gl=ID&ceid=ID:id"
    return feedparser.parse(url)

def find_recent_news():
    satu_hari_lalu = datetime.utcnow() - timedelta(days=1)

    for keyword in CATEGORIES:
        feed = fetch_google_news(keyword)

        for entry in feed.entries:
            if hasattr(entry, "published_parsed"):
                waktu = datetime(*entry.published_parsed[:6])
            else:
                continue

            if waktu > satu_hari_lalu:
                return {
                    "judul": entry.title,
                    "link": entry.link,
                    "ringkasan": entry.summary,
                    "kategori": keyword,
                }

    return None

if __name__ == "__main__":
    hasil = find_recent_news()

    with open("today_news.json", "w", encoding="utf-8") as f:
        json.dump(hasil, f, ensure_ascii=False, indent=2)

    print("Berita ditemukan dan disimpan ke today_news.json" if hasil else "Tidak ada berita terbaru")
