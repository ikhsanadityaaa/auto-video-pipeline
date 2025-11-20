import argparse
import json
import os
import google.generativeai as genai

# Konfigurasi API Key
genai.configure(api_key=os.environ["GEMINI_API_KEY"])

def load_used_topics():
    if not os.path.exists("data/used_topics.json"):
        return []
    try:
        with open("data/used_topics.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return []

def save_used_topic(topic):
    used = load_used_topics()
    used.append(topic)
    os.makedirs("data", exist_ok=True)
    with open("data/used_topics.json", "w", encoding="utf-8") as f:
        json.dump(used, f, indent=2)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--keywords-file", required=True)
    parser.add_argument("--output-script", required=True)
    parser.add_argument("--output-images", required=True)
    args = parser.parse_args()

    with open(args.keywords_file, "r", encoding="utf-8") as f:
        keywords = [k.strip() for k in f if k.strip()]

    used = load_used_topics()
    used_str = "\n".join([f"- {t}" for t in used]) if used else "Belum ada topik yang dipakai."

    prompt = f"""
Kamu adalah asisten konten YouTube otomatis untuk channel bertema:
- Misteri dunia
- Tragedi sejarah
- Eksperimen sains aneh
- Fenomena unik
- Konspirasi faktual
- Penemuan arkeologi
- Kisah mendadak kaya

Daftar keyword yang bisa kamu pilih:  
{', '.join(keywords)}

Daftar topik yang SUDAH PERNAH DIBAHAS (JANGAN PAKAI LAGI):  
{used_str}

TUGASMU:
1. Pilih **satu topik menarik dan faktual** dari keyword di atas.
2. Pastikan topik ini **belum pernah dibahas** (cek daftar di atas).
3. Cari **2–3 artikel dari sumber kredibel** (BBC, Reuters, NatGeo, Smithsonian, History.com, dll) yang **benar-benar membahas hal yang sama** (bukan hanya kategori umum).
4. Buat **narasi video 60 detik dalam BAHASA INDONESIA** dengan:
   - Hook 3 detik di awal (kalimat mengejutkan/pertanyaan)
   - Penjelasan fakta selama 50 detik
   - Penutup 7 detik
5. Hasilkan **4 keyword pencarian gambar faktual** (dalam bahasa Inggris, underscore, fokus pada foto asli).

FORMAT OUTPUT EXACT:
===TOPIC===
[Nama Topik Singkat]
===ARTICLES===
- [Judul 1] | [Link 1]
- [Judul 2] | [Link 2]
===SCRIPT===
[Narasi 60 detik]
===IMAGES===
[keyword1, keyword2, keyword3, keyword4]
"""

    try:
        model = genai.GenerativeModel("gemini-1.0-pro")
        response = model.generate_content(
            prompt,
            safety_settings={
                "HARM_CATEGORY_HARASSMENT": "BLOCK_NONE",
                "HARM_CATEGORY_HATE_SPEECH": "BLOCK_NONE",
                "HARM_CATEGORY_SEXUALLY_EXPLICIT": "BLOCK_NONE",
                "HARM_CATEGORY_DANGEROUS_CONTENT": "BLOCK_NONE"
            }
        )
        text = response.text.strip()

        if "===TOPIC===" not in text:
            raise Exception("Format output tidak sesuai")

        topic = text.split("===TOPIC===")[1].split("===ARTICLES===")[0].strip()
        script = text.split("===SCRIPT===")[1].split("===IMAGES===")[0].strip()
        images_line = text.split("===IMAGES===")[1].strip()
        image_keywords = images_line.replace("[", "").replace("]", "").replace('"', "")

        # Simpan hasil
        with open(args.output_script, "w", encoding="utf-8") as f:
            f.write(script)
        with open(args.output_images, "w", encoding="utf-8") as f:
            f.write(image_keywords)

        # Simpan topik ke riwayat
        save_used_topic(topic)

        print("✅ Topik berhasil dibuat:")
        print(f"Topik: {topic}")
        print(f"Gambar: {image_keywords}")

    except Exception as e:
        print(f"Error Gemini: {e}")
        fallback = "Ada misteri besar yang belum terpecahkan hingga hari ini..."
        with open(args.output_script, "w", encoding="utf-8") as f:
            f.write(fallback)
        with open(args.output_images, "w", encoding="utf-8") as f:
            f.write("mystery,history,science,discovery")

if __name__ == "__main__":
    main()
