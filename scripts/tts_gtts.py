# scripts/tts_gtts.py
from gtts import gTTS
import sys

def make_tts(infile, outfile="voice.mp3"):
    with open(infile, "r", encoding="utf-8") as f:
        text = f.read()
    tts = gTTS(text=text, lang="id")
    tts.save(outfile)
    print("Saved voice:", outfile)

if __name__ == "__main__":
    infile = sys.argv[1] if len(sys.argv) > 1 else "script.txt"
    outfile = sys.argv[2] if len(sys.argv) > 2 else "voice.mp3"
    make_tts(infile, outfile)
