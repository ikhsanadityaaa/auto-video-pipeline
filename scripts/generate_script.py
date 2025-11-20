import argparse
import json
import os
import google.generativeai as genai

# Konfigurasi API Key
genai.configure(api_key=os.environ["GEMINI_API_KEY"])

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--images-out", required=True)
    args = parser.parse_args()

    with open(args.input, "r", encoding="utf-8") as f:
        articles = json.load(f)

    if isinstance(articles, dict) and articles.get("error"):
        print("Fallback: tidak ada berita ditemukan")
        fallback = "Pernahkah kamu dengar tentang: misteri dunia?"
        with open(args.output, "w", encoding="utf-8") as out:
            out.write(fallback)
        with open(args.images-out, "w", encoding="utf-8") as img_out:
            img_out.write("mystery,ancient,history,discovery")
        return

    # Ambil artikel pertama
    first = articles[0] if isinstance(articles, list) else articles
    title = first["title"]
    summary = first["summary"]
    link = first["link"]

    # === PROMPT GEMINI ===
    prompt = f"""
Berdasarkan artikel berikut:

Judul: {title}
Ringkasan: {summary}
Link: {link}

Lakukan hal berikut:
1. Ekstrak topik inti dalam 5-7 kata (misal: "penemuan tiang logam di bawah Piramida Giza").
2. Cari 3 artikel lain dari sumber kredibel (BBC, Reuters, AP, NatGeo, Smithsonian, dll) yang membahas topik YANG SAMA, bukan hanya kategori umum.
3. Buat narasi video 60 detik dalam BAHASA INDONESIA dengan:
   - Hook 3 detik di awal (kalimat mengejutkan atau pertanyaan menarik)
   - Penjelasan fakta selama 50 detik
   - Penutup 7 detik
4. Jangan tambahkan fakta di luar sumber.
5. Hasilkan 4 keyword pencarian gambar faktual (dalam bahasa Inggris, spasi diganti underscore, fokus pada foto asli, bukan ilustrasi).
6. Format output EXACT seperti ini:

===TOPIC===
[TOPIC_INTI]
===ARTICLES===
- [Judul 1] | [Link 1]
- [Judul 2] | [Link 2]
- ...
===SCRIPT===
[Narasi 60 detik]
===IMAGES===
[keyword1, keyword2, keyword3, keyword4]
"""

    try:
        model = genai.GenerativeModel("gemini-1.0-pro")  # ✅ Model yang kompatibel dengan v1beta
        response = model.generate_content(
            prompt,
            safety_settings={
                "HARM_CATEGORY_HARASSMENT": "BLOCK_NONE",
                "HARM_CATEGORY_HATE_SPEECH": "BLOCK_NONE",
                "HARM_CATEGORY_SEXUALLY_EXPLICIT": "BLOCK_NONE",
                "HARM_CATEGORY_DANGEROUS_CONTENT": "BLOCK_NONE"
            }
        )
        full_text = response.text.strip()

        if "===SCRIPT===" in full_text:
            script = full_text.split("===SCRIPT===")[1].split("===IMAGES===")[0].strip()
            image_line = full_text.split("===IMAGES===")[1].strip()
            keywords = image_line.replace("[", "").replace("]", "").replace('"', "")
        else:
            script = "Pernahkah kamu dengar tentang: " + title + "?"
            keywords = "mystery,science,history,discovery"

        with open(args.output, "w", encoding="utf-8") as f:
            f.write(script)
        with open(args.images-out, "w", encoding="utf-8") as f:
            f.write(keywords)
        with open("gemini_full_output.txt", "w", encoding="utf-8") as dbg:
            dbg.write(full_text)

    except Exception as e:
        print(f"Error Gemini: {e}")
        fallback = f"Pernahkah kamu dengar tentang: {title}?"
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(fallback)
        with open(args.images-out, "w", encoding="utf-8") as f:
            f.write("mystery,history,science")

if __name__ == "__main__":
    main()
