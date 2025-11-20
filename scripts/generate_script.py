import argparse
import json
import os
import google.generativeai as genai
# Hapus semua impor tipe objek yang bermasalah (types, HarmCategory, HarmBlockThreshold)
# Hanya impor tipe jika diperlukan, tapi kita akan menghindari objek khusus.

# Konfigurasi API Key
# Pastikan GEMINI_API_KEY sudah diset di GitHub Secrets
try:
    genai.configure(api_key=os.environ["GEMINI_API_KEY"])
except KeyError:
    print("❌ ERROR: Variabel lingkungan GEMINI_API_KEY tidak ditemukan.")
    # Exit jika key tidak ada, karena skrip tidak dapat berjalan tanpa API.
    exit(1)

# Fallback default jika terjadi kegagalan total
FALLBACK_SCRIPT = "Ada kisah misteri yang tersembunyi. Mari kita cari tahu bersama! (Fallback Script)"
FALLBACK_KEYWORDS = ["mystery_archive", "dark_past", "secret_files", "ancient_discovery"]

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, help="JSON file berisi topik query dari fetch_news.py.")
    parser.add_argument("--output", required=True, help="JSON file output akhir (Script & Keywords).")
    args = parser.parse_args()

    # === Load TOPIC QUERY dari skrip fetch_news.py ===
    try:
        with open(args.input, "r", encoding="utf-8") as f:
            topic_query = json.load(f)
    except Exception as e:
        print(f"❌ Error loading input query file: {e}")
        final_output = {"script": FALLBACK_SCRIPT, "keywords": FALLBACK_KEYWORDS}
        with open(args.output, "w", encoding="utf-8") as out:
            json.dump(final_output, out, indent=4, ensure_ascii=False)
        return
        
    # Ambil prompt dan metadata
    gemini_prompt = topic_query.get("gemini_prompt", "")
    topic_type = topic_query.get("topic_type", "UNKNOWN")
    
    if not gemini_prompt:
        print("❌ Error: gemini_prompt tidak ditemukan di file input.")
        final_output = {"script": FALLBACK_SCRIPT, "keywords": FALLBACK_KEYWORDS}
        with open(args.output, "w", encoding="utf-8") as out:
            json.dump(final_output, out, indent=4, ensure_ascii=False)
        return

    # =========================================================
    # 1. DEFINISI STRUKTUR OUTPUT (JSON SCHEMA sebagai Dictionary Standar)
    # =========================================================
    response_schema = {
        "type": "object",
        "properties": {
            "topic": {"type": "string", "description": "Topik utama dalam 5-7 kata."},
            "script": {"type": "string", "description": "Naskah video 60 detik dalam Bahasa Indonesia (termasuk Hook, Body, Closing)."},
            "factual_keywords": {
                "type": "array", 
                "items": {"type": "string"}, 
                "description": "4 kata kunci faktual (nama, lokasi, objek) untuk pencarian gambar. Contoh: 'Titanic wreckage'."
            },
            "illustrative_keywords": {
                "type": "array", 
                "items": {"type": "string"}, 
                "description": "4 kata kunci ilustratif (atmosfir, emosi, vibe) untuk pencarian gambar stock. Contoh: 'dark stormy sea', 'old archive'."
            }
        },
        "required": ["topic", "script", "factual_keywords", "illustrative_keywords"]
    }
    
    # =========================================================
    # 2. PEMANGGILAN API DENGAN GROUNDING
    # =========================================================
    try:
        model = genai.GenerativeModel("gemini-1.5-flash")

        # Konfigurasi Keselamatan (Menggunakan Dictionary Standar)
        safety_settings = [
            {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"}
        ]
        
        # Konfigurasi Tools & Schema (Menggunakan Dictionary Standar)
        tool_config = {
            "tools": [{"google_search": {}}],
            "response_mime_type": "application/json",
            "response_schema": response_schema 
        }

        # Panggil API
        response = model.generate_content(
            gemini_prompt,
            config=tool_config,
            safety_settings=safety_settings 
        )
        
        gemini_output_str = response.text.strip()
        
        # Debug: Simpan output mentah Gemini
        with open("gemini_full_output.json", "w", encoding="utf-8") as dbg:
            dbg.write(gemini_output_str)

        # Parsing JSON
        gemini_output = json.loads(gemini_output_str)

        # === Simpan output akhir ===
        # Gabungkan semua keywords menjadi satu list 
        all_keywords = (
            gemini_output.get("factual_keywords", []) + 
            gemini_output.get("illustrative_keywords", [])
        )
        
        final_output = {
            "title": gemini_output.get("topic", "Topik Tanpa Judul"),
            "script": gemini_output.get("script", FALLBACK_SCRIPT),
            "keywords": all_keywords,
            "topic_type": topic_type,
            "source_info": f"Topic generated by Gemini (Mode: {topic_type})" 
        }
        
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(final_output, f, indent=4, ensure_ascii=False)
            
        print(f"✅ Success! Script for '{final_output['title']}' saved to {args.output}")

    except Exception as e:
        print(f"❌ Error Gemini API Call: {e}")
        # Fallback jika panggilan API gagal total
        fallback_output = {"script": FALLBACK_SCRIPT, "keywords": FALLBACK_KEYWORDS}
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(fallback_output, f, indent=4, ensure_ascii=False)

if __name__ == "__main__":
    main()
