import json
import argparse
import os
import re

def clean_text(text):
    # Hapus HTML & normalisasi spasi
    text = re.sub(r"<.*?>", "", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text

def build_script(article):
    title = clean_text(article.get("title", ""))
    summary = clean_text(article.get("summary", ""))

    # === HOOK 3 DETIK ===
    # Ambil frasa menarik dari judul
    if "mystery" in title.lower() or "misteri" in title.lower():
        hook = "Ada misteri besar yang belum terpecahkan..."
    elif "experiment" in title.lower() or "eksperimen" in title.lower():
        hook = "Ilmuwan baru saja melakukan eksperimen yang mengejutkan..."
    elif "discovery" in title.lower() or "penemuan" in title.lower():
        hook = "Penemuan luar biasa baru saja diumumkan..."
    elif "wealth" in title.lower() or "kaya" in title.lower():
        hook = "Seseorang tiba-tiba menjadi kaya dalam semalam..."
    else:
        hook = f"Pernahkah kamu dengar tentang: {title.split(' - ')[0]}?"

    # === BODY 50 DETIK ===
    # Batasi panjang agar muat ~60 detik
    words = summary.split()
    if len(words) > 180:
        body = " ".join(words[:180]) + "..."
    else:
        body = summary

    # === PENUTUP 7 DETIK ===
    closing = "Simak fakta lengkapnya di video ini."

    script = f"{hook}\n{body}\n{closing}"
    return script

def extract_image_keywords(article):
    title = clean_text(article.get("title", ""))
    # Ambil kata kunci utama: hapus kata umum, keep entitas
    keywords = title.replace(":", "").replace("-", "").replace("discovery", "").replace("mystery", "")
    keywords = re.sub(r"[^a-zA-Z0-9\s]", "", keywords)
    keywords = "_".join(keywords.split()[:4])  # max 4 kata
    return keywords.lower()

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--images-out", required=True)
    args = parser.parse_args()

    with open(args.input, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Ambil artikel pertama (pastikan format list)
    if isinstance(data, list):
        article = data[0]
    elif isinstance(data, dict) and "error" in data:
        # Fallback jika tidak ada berita
        article = {
            "title": "Misteri Dunia yang Belum Terpecahkan",
            "summary": "Banyak misteri di dunia ini belum terpecahkan hingga hari ini. Dari Segitiga Bermuda hingga Voynich Manuscript, para ilmuwan terus mencari jawaban."
        }
    else:
        article = data

    # Buat narasi
    script = build_script(article)
    with open(args.output, "w", encoding="utf-8") as f:
        f.write(script)

    # Buat keyword gambar
    image_kw = extract_image_keywords(article)
    with open(args.images_out, "w", encoding="utf-8") as f:
        f.write(image_kw)

    print("✅ Narasi & keyword gambar berhasil dibuat")

if __name__ == "__main__":
    main()
