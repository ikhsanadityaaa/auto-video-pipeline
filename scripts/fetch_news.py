import argparse
import json
import os
import random
from datetime import datetime, timedelta

# === KONFIGURASI ===
# History tetap dipakai untuk mencatat link AKTUAL yang sudah diproses oleh Gemini.
HISTORY_FILE = "data/news_history.json" 

# Kriteria topik yang akan dimasukkan ke prompt Gemini
TOPIC_CRITERIA = "misteri, kisah tragedi, percobaan science, sejarah, atau konspirasi."

# === FUNGSI BANTU HISTORY (TIDAK BERUBAH) ===

def load_history():
    """Memuat daftar link yang sudah diproses dari history."""
    if not os.path.exists(HISTORY_FILE):
        return set()
    try:
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            # Menggunakan set untuk pencarian cepat
            return set(json.load(f)) 
    except:
        return set()

def save_history(history_set):
    """Menyimpan daftar link yang sudah diproses ke history."""
    os.makedirs("data", exist_ok=True)
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(list(history_set), f, indent=2)

# === FUNGSI PENENTU QUERY GEMINI BARU ===

def create_gemini_query(mode: str, keywords: list, history: set):
    """
    Menyiapkan prompt dan query spesifik untuk Gemini berdasarkan mode.
    
    Returns:
        dict: Objek yang berisi semua parameter untuk panggilan Gemini API.
    """
    
    if mode == "aktual":
        # 1. Tentukan Query untuk Berita Aktual (Mode 06:00 WIB)
        keywords_str = ", ".join(keywords)
        
        # Kirim history ke skrip Gemini selanjutnya agar ia bisa memfilter
        history_str = json.dumps(list(history)) 
        
        gemini_prompt = f"""
        Anda adalah Redaktur Konten. Tugas Anda adalah mencari 1 topik berita **paling aktual (terbit dalam 24 jam terakhir)** yang relevan dengan kriteria: {TOPIC_CRITERIA}.
        
        Fokus pada kata kunci: {keywords_str}.
        
        Nanti, pastikan sumber berita yang dipilih **belum ada** dalam daftar history berikut: {history_str}.
        
        Susun narasinya menjadi skrip video 60 detik. Gunakan alat Grounding (Web Search) secara ekstensif.
        """
        
        print(f"=== READY | QUERY MODE: AKTUAL | Keywords: {keywords_str} ===")
        
        return {
            "topic_type": "AKTUAL",
            "gemini_prompt": gemini_prompt,
            "keywords": keywords,
            "history": list(history)
        }

    elif mode == "masa_lalu":
        # 2. Tentukan Query untuk Kisah Masa Lalu (Mode 16:00 WIB)
        
        # Gunakan kata kunci random untuk variasi topik masa lalu
        past_keywords = ["kisah sejarah terlupakan", "misteri unik tak terpecahkan", "tragedi ilmuwan masa lalu", "temuan arkeologi paling aneh"]
        random_query = random.choice(past_keywords)
        
        gemini_prompt = f"""
        Anda adalah Redaktur Konten. Tugas Anda adalah mencari 1 topik **kisah masa lalu** yang jarang dibahas, memiliki dokumentasi visual (foto/arsip) dan relevan dengan: {TOPIC_CRITERIA}.
        
        Gunakan Grounding (Web Search) untuk menemukan kisah terkait {random_query}.
        
        Susun narasinya menjadi skrip video 60 detik.
        """
        
        print(f"=== READY | QUERY MODE: MASA LALU | Random Query: {random_query} ===")
        
        return {
            "topic_type": "MASA_LALU",
            "gemini_prompt": gemini_prompt,
            "keywords": [random_query]
        }
    
    return None

# === MAIN ===

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    # Tambahkan argumen --mode yang diperlukan di YML
    parser.add_argument("--mode", required=True, choices=["aktual", "masa_lalu"]) 
    parser.add_argument("--keywords-file", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()

    try:
        with open(args.keywords_file, "r", encoding="utf-8") as f:
            keywords = [k.strip() for k in f if k.strip()]
    except FileNotFoundError:
        print("❌ Error: keywords-file tidak ditemukan.")
        exit(1)

    # Muat history (diperlukan untuk mode 'aktual')
    history = load_history()
    
    # Buat Query untuk Gemini
    topic_query = create_gemini_query(args.mode, keywords, history)

    if not topic_query:
        print("❌ Error: Mode tidak valid.")
        with open(args.out, "w", encoding="utf-8") as f:
            json.dump({"error": "invalid_mode"}, f, indent=2)
        exit(1)

    # Simpan Query ke output JSON (Input untuk generate_script.py)
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(topic_query, f, indent=2, ensure_ascii=False)
    
    print(f"✅ Query untuk Gemini tersimpan di {args.out}")
