import argparse
import json
import os
import random
import google.generativeai as genai
# RE-IMPORT: Menggunakan tipe objek API untuk struktur yang tepat
from google.generativeai import types 

# --- Konfigurasi & Utilities ---
HISTORY_FILE = "data/used_topics.json"
TOPIC_CRITERIA = "misteri, kisah sejarah terlupakan, penemuan sains unik, atau tragedi lama."

try:
    genai.configure(api_key=os.environ["GEMINI_API_KEY"])
except KeyError:
    print("❌ ERROR: Variabel lingkungan GEMINI_API_KEY tidak ditemukan.")
    exit(1)

# Fallback default
FALLBACK_SCRIPT = "Ada kisah misteri yang tersembunyi. Mari kita cari tahu bersama! (Fallback Script)"
FALLBACK_KEYWORDS = ["mystery_archive", "dark_past", "secret_files", "ancient_discovery"]

# Helper functions for history (load_history, save_history) remain the same...
def load_history():
    """Memuat daftar topik (berupa judul atau link) yang sudah pernah dibuat."""
    if not os.path.exists(HISTORY_FILE):
        return []
    try:
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return []

def save_history(new_topic_title):
    """Menyimpan judul topik baru ke history."""
    os.makedirs("data", exist_ok=True)
    history = load_history()
    history.append(new_topic_title)
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(history, f, indent=2, ensure_ascii=False)


# === Skema Output (Dictionary Standard - Ini tidak diubah) ===
RESPONSE_SCHEMA_DICT = {
    "type": "object",
    "properties": {
        "topic": {"type": "string", "description": "Judul unik topik yang ditemukan."},
        "script": {"type": "string", "description": "Naskah video 60 detik dalam Bahasa Indonesia (Hook, Body, Closing)."},
        "factual_keywords": {
            "type": "array", 
            "items": {"type": "string"}, 
            "description": "4 kata kunci faktual (nama, lokasi, objek) untuk pencarian gambar."
        },
        "illustrative_keywords": {
            "type": "array", 
            "items": {"type": "string"}, 
            "description": "4 kata kunci ilustratif (atmosfir, emosi, vibe) untuk pencarian gambar stock."
        },
        "source_link": {"type": "string", "description": "Link URL sumber utama informasi ini."}
    },
    "required": ["topic", "script", "factual_keywords", "illustrative_keywords", "source_link"]
}

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

    # 2. Siapkan Prompt Final
    gemini_prompt = f"""
Anda adalah Redaktur Konten. Tugas Anda adalah mencari 1 topik (tidak peduli aktual atau masa lalu) yang unik dan belum pernah dibuat.

Kriteria Topik: Topik harus relevan dengan: {TOPIC_CRITERIA}.
Fokus pada kata kunci: {random_query}.

Pembatasan: Jangan gunakan topik yang judulnya mirip atau sama dengan yang ada di history ini: {history_str}.

Tugas:
1. Cari 1 topik unik (gunakan Grounding/Web Search).
2. Tulis skrip video 60 detik dalam Bahasa Indonesia.
3. Output harus SANGAT ketat dalam format JSON yang diminta.
"""
    
    # 3. Panggil Gemini API
    try:
        model = genai.GenerativeModel("gemini-1.5-flash")

        # FIX: Bungkus semua konfigurasi ke dalam objek types.GenerateContentConfig
        # Ini adalah cara yang benar sesuai dokumentasi modern.
        full_config = types.GenerateContentConfig(
            tools=[{"google_search": {}}],
            response_mime_type="application/json",
            response_schema=RESPONSE_SCHEMA_DICT
        )

        # Panggil API dengan config dan safety_settings
        response = model.generate_content(
            contents=gemini_prompt, # Gunakan contents jika passing keyword lain
            config=full_config,     # Gunakan keyword 'config'
            safety_settings=SAFETY_SETTINGS 
        )
        
        gemini_output_str = response.text.strip()
        
        # Debug: Simpan output mentah Gemini
        with open("gemini_full_output.json", "w", encoding="utf-8") as dbg:
            dbg.write(gemini_output_str)

        # Parsing JSON
        gemini_output = json.loads(gemini_output_str)

        # 4. Simpan Output dan Update History
        
        all_keywords = (
            gemini_output.get("factual_keywords", []) + 
            gemini_output.get("illustrative_keywords", [])
        )
        
        final_output = {
            "title": gemini_output.get("topic", "Topik Tak Dikenal"),
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
        print(f"❌ Error Gemini API Call: {e}")
        # Fallback
        fallback_output = {"script": "Fallback Error Script", "keywords": []}
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(fallback_output, f, indent=4, ensure_ascii=False)

if __name__ == "__main__":
    main()
