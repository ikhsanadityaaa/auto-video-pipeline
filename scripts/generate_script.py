import argparse
import json
import os
import random
import google.generativeai as genai

# --- Konfigurasi & Utilities ---
HISTORY_FILE = "data/used_topics.json"
TOPIC_CRITERIA = "misteri, kisah sejarah terlupakan, penemuan sains unik, atau tragedi lama."
# Marker untuk memudahkan parsing
JSON_START_MARKER = "===JSON_START==="
JSON_END_MARKER = "===JSON_END==="

# Coba Konfigurasi API Key
try:
    # Memastikan API Key diatur
    API_KEY = os.environ["GEMINI_API_KEY"]
    if not API_KEY:
         raise ValueError("GEMINI_API_KEY kosong.")
    genai.configure(api_key=API_KEY)
except (KeyError, ValueError, AttributeError) as e:
    print(f"❌ ERROR KRITIS: API Key tidak dapat dikonfigurasi. {e}")
    exit(1)


# Fallback default
FALLBACK_SCRIPT = "Ada kisah misteri yang tersembunyi. Mari kita cari tahu bersama! (Fallback Script)"

def load_history():
    # ... (fungsi tetap sama) ...
    if not os.path.exists(HISTORY_FILE):
        return []
    try:
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return []

def save_history(new_topic_title):
    # ... (fungsi tetap sama) ...
    os.makedirs("data", exist_ok=True)
    history = load_history()
    history.append(new_topic_title)
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(history, f, indent=2, ensure_ascii=False)


# Karena safety_settings sering menimbulkan error di versi lama, kita akan kirimkannya
# ke API hanya jika API menerima, jika tidak, kita akan mengabaikannya di blok try/except.
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
    history_str = json.dumps(history, ensure_ascii=False)
    random_query = random.choice(keywords)

    # 2. Siapkan Prompt Final
    gemini_prompt = f"""
Anda adalah Redaktur Konten. Tugas Anda adalah mencari 1 topik unik (tidak peduli aktual/masa lalu) yang belum pernah dibuat.

Instruksi:
1. **Gunakan pengetahuan internal dan pencarian berbasis teks** untuk menemukan topik yang relevan dengan: {TOPIC_CRITERIA}.
2. Fokus pada kata kunci: {random_query}.
3. Jangan gunakan topik yang judulnya mirip atau sama dengan yang ada di history ini: {history_str}.
4. Tulis skrip video 60 detik dalam Bahasa Indonesia.
5. Setelah skrip, output JSON yang berisi semua data, bungkus di antara penanda '{JSON_START_MARKER}' dan '{JSON_END_MARKER}'.

FORMAT OUTPUT:
[Skrip lengkap di sini]

{JSON_START_MARKER}
{{
    "title": "Judul Unik Topik",
    "script": "Naskah video 60 detik...",
    "factual_keywords": ["keyword1", "keyword2", "keyword3", "keyword4"],
    "illustrative_keywords": ["keyword_illus1", "keyword_illus2", "keyword_illus3", "keyword_illus4"],
    "source_link": "URL Sumber Utama (Berikan link aktual yang Anda temukan)"
}}
{JSON_END_MARKER}
"""
    
    # 3. Panggil Gemini API
    try:
        # Coba Model Paling Universal jika 1.5-flash gagal di lingkungan lama
        model = genai.GenerativeModel("gemini-pro")

        # Panggil API hanya dengan parameter SANGAT DASAR
        try:
            # Coba panggil dengan safety settings (jika API mengenali)
            response = model.generate_content(
                contents=gemini_prompt,
                safety_settings=SAFETY_SETTINGS
            )
        except Exception:
            # Jika safety_settings gagal (karena versi terlalu usang), coba tanpa safety settings
            print("Peringatan: safety_settings diabaikan karena API tidak mengenali argumen tersebut.")
            response = model.generate_content(
                contents=gemini_prompt
            )
        
        gemini_output_str = response.text.strip()
        
        # Debug: Simpan output mentah Gemini
        with open("gemini_full_output.json", "w", encoding="utf-8") as dbg:
            dbg.write(gemini_output_str)

        # 4. Parsing Teks untuk Mengekstrak JSON
        if JSON_START_MARKER not in gemini_output_str:
            raise ValueError(f"Output Gemini tidak mengandung penanda JSON. Output: {gemini_output_str[:200]}...")
        
        json_text = gemini_output_str.split(JSON_START_MARKER, 1)[1]
        json_text = json_text.split(JSON_END_MARKER, 1)[0].strip()

        # Membersihkan blok kode Markdown
        json_text = json_text.strip("```json").strip().strip("```").strip()

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
        
        save_history(final_output['title'])

        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(final_output, f, indent=4, ensure_ascii=False)
            
        print(f"✅ Success! Script for '{final_output['title']}' saved to {args.output}")

    except Exception as e:
        print(f"❌ Error Gemini API Call/Parsing: {e}")
        # Fallback jika panggilan API gagal total
        fallback_output = {"script": "Fallback Error Script", "keywords": []}
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(fallback_output, f, indent=4, ensure_ascii=False)

if __name__ == "__main__":
    main()
