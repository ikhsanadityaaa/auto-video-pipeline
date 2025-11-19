# scripts/tiktok_playwright.py
from playwright.sync_api import sync_playwright
import sys, json, os

def run(video_path, caption=""):
    state_file = os.environ.get("TIKTOK_STATE", "tiktok_state.json")
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        # restore storage state if exists
        if os.path.exists(state_file):
            context = browser.new_context(storage_state=state_file)
        page = context.new_page()
        page.goto("https://www.tiktok.com/upload")
        # upload file
        page.set_input_files("input[type='file']", video_path)
        # fill caption
        page.fill("textarea", caption)
        print("TikTok upload prepared. Please click Post in the opened browser window.")
        # keep browser open
        page.wait_for_timeout(5*60*1000)  # wait 5 minutes for manual click
        # optionally save storage
        context.storage_state(path=state_file)
        browser.close()

if __name__ == "__main__":
    video = sys.argv[1] if len(sys.argv) > 1 else "final.mp4"
    caption = sys.argv[2] if len(sys.argv) > 2 else ""
    run(video, caption)
