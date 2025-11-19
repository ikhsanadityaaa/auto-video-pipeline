import argparse
import json
import os
import random
from datetime import datetime, timedelta

# Lokasi penyimpanan history (Tetap dipakai untuk link aktual yang sudah diolah)
# Kita tetap perlu file ini untuk memastikan Gemini tidak mengolah link berita yang SAMA dua kali.
HISTORY_FILE = "data/news_history.json"

# ==================================================
# LOAD / SAVE HISTORY (Untuk mencatat link aktual yang sudah diproses)
# ==================================================
def load_history():
    """Memuat daftar link yang sudah diproses dari history."""
    if not os.path.exists(HISTORY_FILE):
        return []
    try:
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return []

def save_history(history):
    """Menyimpan daftar link yang sudah diproses ke history."""
    os.makedirs("data", exist_ok=True)
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(history, f, indent=4)

# ==================================================
# FUNGSI PENENTU QUERY GEMINI
# ==================================================

def create_gemini_query(mode: str, keywords: list, history: list):
    """
    Menyiapkan prompt dan query spesifik berdasarkan mode.

    Args:
        mode (str): 'aktual' atau 'masa_lalu'
        keywords (list): Daftar kata kunci utama (misteri, sains, dll.)
        history (list): Daftar link berita yang sudah diproses.
    
    Returns:
        dict: Objek yang berisi semua parameter untuk panggilan Gemini API.
    """
    
    # Kriteria topik Anda yang akan dimasukkan ke prompt Gemini
    topic_criteria = "misteri, kisah tragedi, percobaan science, sejarah, atau konspirasi."
    
    if mode == "aktual":
        # 1. Tentukan Query untuk Berita Aktual
        query_type = "AKTUAL"
        
        # Kata kunci yang dicari (dapat ditambahkan ke prompt)
        keywords_str = ", ".join(keywords)
        
        # Instruksi utama untuk Gemini. Penting: Gunakan Grounding (Web Search)
        gemini_prompt = f"""
        Anda adalah Redaktur Konten. Tugas Anda adalah mencari 1 topik berita **paling aktual (terbit dalam 24 jam terakhir)** yang relevan dengan kriteria: {topic_criteria}.
        
        Fokus pada kata kunci: {keywords_str}.
        
        Setelah menemukan topik, susun narasinya menjadi skrip video 60 detik dengan hook 3 detik dramatis. 
        Pastikan sumber berita yang dipilih **belum pernah diproses** (cek history).
        
        Jika tidak ada berita aktual yang relevan, keluarkan JSON dengan "topic_type": "AKTUAL_GAGAL".
        """
        
        print("=== MODE AKTUAL | MENGGUNAKAN GEMINI UNTUK PENCARIAN & SCRIPTING AKTUAL ===")
        
        return {
            "topic_type": query_type,
            "gemini_prompt": gemini_prompt,
            "history": history # Kirim history ke Gemini agar ia bisa memfilter
        }

    elif mode == "masa_lalu":
        # 2. Tentukan Query untuk Kisah Masa Lalu
        query_type = "MASA_LALU"
        
        # Gunakan kata kunci random untuk variasi topik masa lalu
        past_keywords = ["kisah sejarah terlupakan", "misteri unik tak terpecahkan", "tragedi ilmuwan masa lalu"]
        random_query = random.choice(past_keywords)
        
        gemini_prompt = f"""
        Anda adalah Redaktur Konten. Tugas Anda adalah mencari 1 topik **kisah masa lalu** yang jarang dibahas, memiliki dokumentasi visual (foto/arsip) dan relevan dengan: {topic_criteria}.
        
        Contoh topik: {random_query}.
        
        Susun narasinya menjadi skrip video 60 detik dengan hook 3 detik dramatis.
        """
        
        print("=== MODE MASA LALU | MENGGUNAKAN GEMINI UNTUK PENCARIAN & SCRIPTING MASA LALU ===")
        
        return {
            "topic_type": query_type,
            "gemini_prompt": gemini_prompt,
            "history": [] # History tidak relevan untuk topik masa lalu yang dicari secara acak
        }
    
    return None

# ==================================================
# MAIN EXECUTION
# ==================================================
if __name__ == "__main__":
    
    parser = argparse.ArgumentParser()
    # Mode ini menentukan jenis prompt yang akan dikirim ke Gemini
    parser.add_argument("--mode", required=True, choices=["aktual", "masa_lalu"])
    parser.add_argument("--keywords-file", required=True)
    parser.add_argument("--out", required=True, help="File output JSON untuk input Gemini Scripting.")
    args = parser.parse_args()

    # Muat keyword
    try:
        with open(args.keywords_file, "r", encoding="utf-8") as f:
            keywords = [x.strip() for x in f.readlines() if x.strip()]
    except FileNotFoundError:
        print("Error: keywords-file tidak ditemukan.")
        exit(1)

    # Muat history (untuk filter aktual)
    history = load_history()
    
    # 1. Buat Query Utama
    topic_query = create_gemini_query(args.mode, keywords, history)

    if not topic_query:
        print("Error: Mode tidak valid.")
        exit(1)

    # Catatan: Logika cadangan harus diimplementasikan di skrip berikutnya (Scripting dengan Gemini)
    # Skrip ini hanya menghasilkan satu query.

    # Simpan ke output (Input untuk langkah Gemini Scripting)
    print(f"=== READY | OUTPUTTING QUERY FOR GEMINI: {topic_query['topic_type']} ===")

    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(topic_query, f, indent=4, ensure_ascii=False)
