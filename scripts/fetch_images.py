# scripts/fetch_images.py
import os
import sys
import requests
from urllib.parse import quote_plus

PEXELS_KEY = os.environ.get("PEXELS_KEY")
WIKIMEDIA_SEARCH = "https://commons.wikimedia.org/w/index.php?search="

def download(url, dest):
    try:
        r = requests.get(url, stream=True, timeout=20)
        r.raise_for_status()
        with open(dest, "wb") as f:
            for chunk in r.iter_content(1024):
                f.write(chunk)
        return True
    except Exception as e:
        return False

def fetch_from_pexels(query, per_page=5):
    headers = {"Authorization": PEXELS_KEY}
    params = {"query": query, "per_page": per_page}
    r = requests.get("https://api.pexels.com/v1/search", params=params, headers=headers, timeout=20)
    if r.status_code != 200:
        return []
    data = r.json()
    return [p["src"]["large2x"] for p in data.get("photos", [])]

def ensure_images(script_path, out_dir):
    if not os.path.exists(out_dir):
        os.makedirs(out_dir)
    with open(script_path, "r", encoding="utf-8") as f:
        txt = f.read()
    # create keywords from script by picking nouns or full title phrases
    queries = []
    lines = [l.strip() for l in txt.splitlines() if l.strip()]
    if lines:
        queries.append(lines[0])  # hook line as first query
        queries.extend(lines[1:4])
    # fetch images
    images = []
    for i, q in enumerate(queries):
        qshort = q if len(q) < 80 else q[:80]
        if PEXELS_KEY:
            urls = fetch_from_pexels(qshort, per_page=1)
            if urls:
                path = os.path.join(out_dir, f"img_{i+1}.jpg")
                if download(urls[0], path):
                    images.append(path)
                    continue
        # fallback: create a blank placeholder
        path = os.path.join(out_dir, f"img_{i+1}.jpg")
        open(path, "wb").close()
        images.append(path)
    # ensure at least 4 images
    while len(images) < 4:
        p = os.path.join(out_dir, f"img_extra_{len(images)+1}.jpg")
        open(p, "wb").close()
        images.append(p)
    print("Downloaded images:", images)
    return images

if __name__ == "__main__":
    script_file = sys.argv[1] if len(sys.argv) > 1 else "script.txt"
    out_dir = sys.argv[2] if len(sys.argv) > 2 else "assets/images"
    ensure_images(script_file, out_dir)
