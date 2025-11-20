import os
import argparse
import json
import google.generativeai as genai

# Konfigurasi API Key
genai.configure(api_key=os.environ["GEMINI_API_KEY"])

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--images-out", required=True)
    args = parser.parse_args()

    # Baca input
    with open(args.input, "r", encoding="utf-8") as f:
        articles = json.load(f)

    # Cek error
    if isinstance(articles, dict) and articles.get("error"):
        script = "Tidak ada berita ditemukan. Menggunakan topik fallback..."
        keywords = "mystery,science,history,discovery"
    else:
        # Ambil artikel pertama
        article = articles[0] if isinstance(articles, list) else articles
        prompt = f"""
Berdasarkan artikel ini:
Judul: {article.get('title', 'Tidak ada judul')}
Ringkasan: {article.get('summary', 'Tidak ada ringkasan')}

Buat narasi video 60 detik dalam BAHASA INDONESIA dengan:
- Hook 3 detik di awal (kalimat mengejutkan)
- Penjelasan faktual
- Penutup singkat
- Jangan tambahkan fakta di luar artikel
- Hasilkan 4 keyword pencarian gambar (bahasa Inggris, underscore)

Format output:
===SCRIPT===
[Narasi]
===IMAGES===
[keyword1, keyword2, keyword3, keyword4]
"""

        # Gunakan model yang benar
        model = genai.GenerativeModel("gemini-1.5-flash")
        try:
            response = model.generate_content(prompt, safety_settings={
                "HARM_CATEGORY_HARASSMENT": "BLOCK_NONE",
                "HARM_CATEGORY_HATE_SPEECH": "BLOCK_NONE",
                "HARM_CATEGORY_SEXUALLY_EXPLICIT": "BLOCK_NONE",
                "HARM_CATEGORY_DANGEROUS_CONTENT": "BLOCK_NONE"
            })
            full_text = response.text
        except Exception as e:
            print("Error dari Gemini:", str(e))
            full_text = "Pernahkah kamu dengar tentang: " + article.get("title", "misteri dunia") + "?"

        if "===SCRIPT===" in full_text:
            script = full_text.split("===SCRIPT===")[1].split("===IMAGES===")[0].strip()
            img_part = full_text.split("===IMAGES===")[1].strip()
            keywords = img_part.replace("[", "").replace("]", "").replace('"', "")
        else:
            script = full_text if full_text else "Tidak ada narasi."
            keywords = "mystery,science,history,discovery"

    # Simpan output
    with open(args.output, "w", encoding="utf-8") as f:
        f.write(script)
    with open(args.images_out, "w", encoding="utf-8") as f:
        f.write(keywords)

if __name__ == "__main__":
    main()
