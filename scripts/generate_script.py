import argparse
import json
import os
import random
import google.generativeai as genai
# Hapus semua impor tipe objek (types, HarmCategory, dll.)

# --- Konfigurasi & Utilities ---
HISTORY_FILE = "data/used_topics.json"
TOPIC_CRITERIA = "misteri, kisah sejarah terlupakan, penemuan sains unik, atau tragedi lama."
# Marker untuk memudahkan parsing
JSON_START_MARKER = "===JSON_START==="
JSON_END_MARKER = "===JSON_END==="

try:
    genai.configure(api_key=os.environ["GEMINI_API_KEY"])
except KeyError:
    print("❌ ERROR: Variabel lingkungan GEMINI_API_KEY tidak ditemukan.")
    exit(1)

# Fallback default
FALLBACK_SCRIPT = "Ada kisah misteri yang tersembunyi. Mari kita cari tahu bersama! (Fallback Script)"

def load_history():
    if not os.path.exists(HISTORY_FILE):
        return []
    try:
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return []

def save_history(new_topic_title):
    os.makedirs("data", exist_ok=True)
    history = load_history()
    history.append(new_topic_title)
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(history, f, indent=2, ensure_ascii=False)


# Konfigurasi Keselamatan (Dictionary Standar)
SAFETY_SETTINGS = [
    {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"}
]

# === MAIN FUNCTION ===

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--keywords-file", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    # 1. Muat Keywords & History
    try:
        with open(args.keywords_file, "r", encoding="utf-8") as f:
            keywords = [k.strip() for k in f if k.strip()]
    except FileNotFoundError:
        print("❌ Error: keywords-file tidak ditemukan.")
        exit(1)
    
    history = load_history()
    history_str = json.dumps(history)
    random_query = random.choice(keywords)

    # 2. Siapkan Prompt Final (Meminta JSON di dalam marker)
    gemini_prompt = f"""
Anda adalah Redaktur Konten. Tugas Anda adalah mencari 1 topik unik yang belum pernah dibuat.

Kriteria Topik: Topik harus relevan dengan: {TOPIC_CRITERIA}.
Fokus pada kata kunci: {random_query}.

Pembatasan: Jangan gunakan topik yang judulnya mirip atau sama dengan yang ada di history ini: {history_str}.

Tugas:
1. Cari 1 topik unik (gunakan Grounding/Web Search).
2. Tulis skrip video 60 detik dalam Bahasa Indonesia.
3. Setelah skrip selesai, output JSON yang berisi semua data, bungkus di antara penanda '{JSON_START_MARKER}' dan '{JSON_END_MARKER}'.

FORMAT OUTPUT:
[Skrip lengkap di sini]

{JSON_START_MARKER}
{{
    "title": "Judul Unik Topik",
    "script": "Naskah video 60 detik...",
    "factual_keywords": ["keyword1", "keyword2", "keyword3", "keyword4"],
    "illustrative_keywords": ["keyword_illus1", "keyword_illus2", "keyword_illus3", "keyword_illus4"],
    "source_link": "URL Sumber Utama"
}}
{JSON_END_MARKER}
"""
    
    # 3. Panggil Gemini API
    try:
        model = genai.GenerativeModel("gemini-1.5-flash")

        # Panggil API hanya dengan parameter dasar yang dijamin bekerja.
        response = model.generate_content(
            contents=gemini_prompt,
            tools=[{"google_search": {}}], # Parameter tools
            safety_settings=SAFETY_SETTINGS
        )
        
        gemini_output_str = response.text.strip()
        
        # Debug: Simpan output mentah Gemini
        with open("gemini_full_output.json", "w", encoding="utf-8") as dbg:
            dbg.write(gemini_output_str)

        # 4. Parsing Teks untuk Mengekstrak JSON
        if JSON_START_MARKER not in gemini_output_str:
            raise ValueError("Output Gemini tidak mengandung penanda JSON.")
        
        # Ambil teks antara penanda
        json_text = gemini_output_str.split(JSON_START_MARKER, 1)[1]
        json_text = json_text.split(JSON_END_MARKER, 1)[0].strip()

        # Membersihkan blok kode Markdown (jika ada)
        if json_text.startswith("```json"):
            json_text = json_text.strip("```json").strip()
        if json_text.endswith("```"):
            json_text = json_text.strip("```").strip()

        gemini_output = json.loads(json_text)

        # 5. Simpan Output dan Update History
        
        all_keywords = (
            gemini_output.get("factual_keywords", []) + 
            gemini_output.get("illustrative_keywords", [])
        )
        
        final_output = {
            "title": gemini_output.get("title", "Topik Tak Dikenal"),
            "script": gemini_output.get("script", FALLBACK_SCRIPT),
            "keywords": all_keywords,
            "source_link": gemini_output.get("source_link", "URL Not Provided"),
        }
        
        # Simpan topik baru ke history
        save_history(final_output['title'])

        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(final_output, f, indent=4, ensure_ascii=False)
            
        print(f"✅ Success! Script for '{final_output['title']}' saved to {args.output}")

    except Exception as e:
        print(f"❌ Error Gemini API Call/Parsing: {e}")
        # Fallback
        fallback_output = {"script": "Fallback Error Script", "keywords": []}
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(fallback_output, f, indent=4, ensure_ascii=False)

if __name__ == "__main__":
    main()
