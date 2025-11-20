import argparse
import json
import os
import google.generativeai as genai

# Konfigurasi API Key
genai.configure(api_key=os.environ["GEMINI_API_KEY"])

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--images-out", required=True)
    args = parser.parse_args()

    # === Load artikel ===
    with open(args.input, "r", encoding="utf-8") as f:
        articles = json.load(f)

    # === Jika tidak ada berita ===
    if isinstance(articles, dict) and articles.get("error"):
        print("Fallback: tidak ada berita ditemukan")
        fallback_script = "Pernahkah kamu dengar salah satu misteri terbesar dunia?"
        fallback_keywords = "mystery,ancient_history,science_discovery,archive_photo"

        with open(args.output, "w", encoding="utf-8") as out:
            out.write(fallback_script)
        with open(args.images_out, "w", encoding="utf-8") as img_out:
            img_out.write(fallback_keywords)
        return

    # === Ambil artikel pertama ===
    first = articles[0] if isinstance(articles, list) else articles
    title = first.get("title", "")
    summary = first.get("summary", "")
    link = first.get("link", "")

    # === Prompt Gemini ===
    prompt = f"""
You are an expert researcher and documentary scriptwriter.

Use the article below:

TITLE: {title}
SUMMARY: {summary}
LINK: {link}

TASK:
1. Extract the MAIN TOPIC in 5–7 words.
2. Identify 3 other reputable news articles discussing THE SAME specific topic. 
   - They must be contextually the same topic, not just similar category.
   - If cannot find, write "NONE".
3. Write a 60-second video script in Bahasa Indonesia:
   - 3-sec hook (shocking question or surprising fact)
   - 50 sec explanation (pure factual)
   - 7 sec closing
4. Do NOT invent fake facts outside the available information.
5. Produce 4 factual image search keywords (English, underscore instead of spaces).
6. Output EXACTLY in this format:

===TOPIC===
[topic]
===ARTICLES===
- [Title 1] | [URL 1]
- [Title 2] | [URL 2]
- [Title 3] | [URL 3]
===SCRIPT===
[script here]
===IMAGES===
[keyword1, keyword2, keyword3, keyword4]
"""

    try:
        model = genai.GenerativeModel("gemini-1.5-flash")

        response = model.generate_content(
            prompt,
            safety_settings={
                "HARM_CATEGORY_HARASSMENT": "BLOCK_NONE",
                "HARM_CATEGORY_HATE_SPEECH": "BLOCK_NONE",
                "HARM_CATEGORY_SEXUALLY_EXPLICIT": "BLOCK_NONE",
                "HARM_CATEGORY_DANGEROUS_CONTENT": "BLOCK_NONE"
            }
        )

        full_text = response.text.strip()
        with open("gemini_full_output.txt", "w", encoding="utf-8") as dbg:
            dbg.write(full_text)

        # === Parse output ===
        if "===SCRIPT===" in full_text and "===IMAGES===" in full_text:
            script = full_text.split("===SCRIPT===")[1].split("===IMAGES===")[0].strip()
            image_line = full_text.split("===IMAGES===")[1].strip()

            keywords = (
                image_line.replace("[", "")
                .replace("]", "")
                .replace('"', "")
                .replace(" ", "")
            )
        else:
            script = f"Pernahkah kamu dengar tentang {title}?"
            keywords = "mystery,science,history,archive"

        # === Simpan output ===
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(script)

        with open(args.images_out, "w", encoding="utf-8") as f:
            f.write(keywords)

    except Exception as e:
        print(f"Error Gemini: {e}")
        fallback = f"Pernahkah kamu dengar tentang {title}?"
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(fallback)
        with open(args.images_out, "w", encoding="utf-8") as f:
            f.write("mystery,ancient,science,history")

if __name__ == "__main__":
    main()
