import argparse
import json
import os
import google.generativeai as genai
from google.generativeai import types
from google.generativeai.types import HarmCategory, HarmBlockThreshold

# Konfigurasi API Key
genai.configure(api_key=os.environ["GEMINI_API_KEY"])

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, help="JSON file berisi topik yang akan diproses.")
    parser.add_argument("--output", required=True, help="JSON file output (Script & Keywords).")
    args = parser.parse_args()

    # Fallback default jika terjadi kegagalan total
    FALLBACK_SCRIPT = "Ada kisah misteri yang tersembunyi. Mari kita cari tahu bersama!"
    FALLBACK_KEYWORDS = ["mystery_archive", "dark_past", "secret_files", "ancient_discovery"]

    # === Load topik/artikel dari skrip sebelumnya ===
    try:
        with open(args.input, "r", encoding="utf-8") as f:
            topic_data = json.load(f)
    except Exception as e:
        print(f"Error loading input file: {e}")
        # Jika file input gagal dimuat, langsung fallback
        final_output = {"script": FALLBACK_SCRIPT, "keywords": FALLBACK_KEYWORDS}
        with open(args.output, "w", encoding="utf-8") as out:
            json.dump(final_output, out, indent=4)
        return

    # Ambil data link/title yang dikirim dari skrip sebelumnya
    title = topic_data.get("title", "Unknown Topic")
    link = topic_data.get("link", "NONE")
    topic_type = topic_data.get("type", "UNKNOWN")

    # =========================================================
    # 1. DEFINISI STRUKTUR OUTPUT (JSON SCHEMA)
    # =========================================================
    # Ini menjamin output Gemini selalu terstruktur, anti-parsing error!
    response_schema = types.Schema(
        type=types.Type.OBJECT,
        properties={
            "topic": types.Schema(type=types.Type.STRING, description="Topik utama dalam 5-7 kata."),
            "script": types.Schema(type=types.Type.STRING, description="Naskah video 60 detik dalam Bahasa Indonesia (termasuk Hook, Body, Closing)."),
            "factual_keywords": types.Schema(type=types.Type.ARRAY, items=types.Schema(type=types.Type.STRING), description="4 kata kunci faktual (nama, lokasi, objek) untuk pencarian gambar."),
            "illustrative_keywords": types.Schema(type=types.Type.ARRAY, items=types.Schema(type=types.Type.STRING), description="4 kata kunci ilustratif (atmosfir, emosi, vibe) untuk pencarian gambar stock.")
        },
        required=["topic", "script", "factual_keywords", "illustrative_keywords"]
    )
    
    # =========================================================
    # 2. PROMPT GEMINI (Menggunakan Grounding)
    # =========================================================
    prompt = f"""
Anda adalah peneliti dan penulis naskah dokumenter. Anda harus bekerja berdasarkan topik yang diberikan.

MODE TOPIK: {topic_type}

INFORMASI SUMBER:
- JUDUL: {title}
- LINK: {link}

TUGAS:
1. VERIFIKASI: Gunakan alat pencarian web (Grounding) untuk memverifikasi topik dan mencari detail tambahan.
2. SCRIPT: Tulis naskah video 60 detik dalam Bahasa Indonesia: Hook 3 detik dramatis, Body 50 detik faktual (gunakan data web dari Grounding), Closing 7 detik.
3. KEYWORDS: Sediakan 4 kata kunci FAKTUAL (spesifik) dan 4 kata kunci ILUSTRATIF (atmosfir) untuk pencarian gambar.

JANGAN MENGINVENSI FAKTA. PASTIKAN SEMUA OUTPUT DALAM FORMAT JSON yang diminta.
"""

    try:
        model = genai.GenerativeModel("gemini-1.5-flash")

        # Konfigurasi Keselamatan
        safety_settings = [
            types.SafetySetting(category=HarmCategory.HARM_CATEGORY_HARASSMENT, threshold=HarmBlockThreshold.BLOCK_NONE),
            types.SafetySetting(category=HarmCategory.HARM_CATEGORY_HATE_SPEECH, threshold=HarmBlockThreshold.BLOCK_NONE),
            types.SafetySetting(category=HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT, threshold=HarmBlockThreshold.BLOCK_NONE),
            types.SafetySetting(category=HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT, threshold=HarmBlockThreshold.BLOCK_NONE)
        ]

        # Konfigurasi Tools: Mengaktifkan Google Search (Grounding)
        tool_config = types.GenerateContentConfig(
            tools=[{"google_search": {}}],
            response_mime_type="application/json",
            response_schema=response_schema
        )

        response = model.generate_content(
            prompt,
            config=tool_config,
            safety_settings=safety_settings
        )
        
        # Output Gemini adalah string JSON
        gemini_output_str = response.text.strip()
        
        # Debug: Simpan output mentah Gemini
        with open("gemini_full_output.json", "w", encoding="utf-8") as dbg:
            dbg.write(gemini_output_str)

        # Parsing JSON (dijamin berhasil karena menggunakan response_schema)
        gemini_output = json.loads(gemini_output_str)

        # === Simpan output akhir (Script & Keywords digabung) ===
        # Gabungkan semua keywords menjadi satu list untuk proses berikutnya
        all_keywords = (
            gemini_output["factual_keywords"] + 
            gemini_output["illustrative_keywords"]
        )
        
        final_output = {
            "title": gemini_output["topic"],
            "script": gemini_output["script"],
            "keywords": all_keywords,
            "source_link": link # Simpan link sumber asli untuk kredit
        }
        
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(final_output, f, indent=4, ensure_ascii=False)
            
        print(f"✅ Success! Script for '{final_output['title']}' saved to {args.output}")

    except Exception as e:
        print(f"Error Gemini API Call: {e}")
        # Fallback jika panggilan API gagal total
        fallback_output = {"script": FALLBACK_SCRIPT, "keywords": FALLBACK_KEYWORDS}
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(fallback_output, f, indent=4, ensure_ascii=False)

if __name__ == "__main__":
    main()
