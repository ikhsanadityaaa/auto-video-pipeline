# scripts/generate_script.py
import os
import argparse
import json
import google.generativeai as genai

genai.configure(api_key=os.environ["GEMINI_API_KEY"])

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--images-out", required=True)
    args = parser.parse_args()

    with open(args.input, "r") as f:
        data = json.load(f)

    # Cek error
    if isinstance(data, dict) and data.get("error"):
        script = "Tidak ada berita ditemukan. Menggunakan topik fallback..."
        keywords = "mystery,ancient,history"
    else:
        # Ambil artikel pertama
        article = data[0] if isinstance(data, list) else data
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

        model = genai.GenerativeModel("gemini-1.5-flash")
        response = model.generate_content(prompt).text

        if "===SCRIPT===" in response:
            script = response.split("===SCRIPT===")[1].split("===IMAGES===")[0].strip()
            img_part = response.split("===IMAGES===")[1].strip()
            keywords = img_part.replace("[", "").replace("]", "").replace('"', "")
        else:
            script = "Pernahkah kamu dengar tentang: " + article.get("title", "misteri dunia") + "?"
            keywords = "mystery,science,history,discovery"

    with open(args.output, "w", encoding="utf-8") as f:
        f.write(script)
    with open(args.images-out, "w", encoding="utf-8") as f:
        f.write(keywords)

if __name__ == "__main__":
    main()
