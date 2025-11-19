# scripts/generate_script.py
import json
import sys
import textwrap
import re

def simple_clean(html):
    txt = re.sub(r'<[^>]+>', '', html)
    txt = txt.replace('\n', ' ').strip()
    return txt

def summarize_text(text, max_words=220):
    words = text.split()
    if len(words) <= max_words:
        return text
    return ' '.join(words[:max_words]) + '...'

def build_narrative(item):
    title = item.get("title", "")
    summary = simple_clean(item.get("summary", ""))
    body = summarize_text(summary, max_words=180)
    # Hook 3 detik: pendek dan memancing
    hook = f"Pernah dengar tentang {title.split(' - ')[0]}?"
    # full script ~60 detik target
    script = hook + "\n\n" + body + "\n\nSumber: " + item.get("link", "")
    return script

if __name__ == "__main__":
    infile = "topic.json"
    if len(sys.argv) > 1:
        infile = sys.argv[1]
    with open(infile, "r", encoding="utf-8") as f:
        data = json.load(f)
    # choose first item if exists
    if not data:
        print("No topic found")
        sys.exit(1)
    item = data[0]
    script = build_narrative(item)
    with open(sys.argv[2] if len(sys.argv) > 2 else "script.txt", "w", encoding="utf-8") as out:
        out.write(script)
    print("Wrote script.txt")
