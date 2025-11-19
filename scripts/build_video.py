# scripts/build_video.py
import sys
import os
import subprocess
from pathlib import Path

def build(images_dir, voice_file, sfx_shutter, sfx_flash, bg_music, out_file):
    imgs = sorted([str(p) for p in Path(images_dir).glob("*.jpg")])
    if not imgs:
        raise SystemExit("No images found in " + images_dir)
    # durations: equal split
    total_dur = 60.0
    per = total_dur / len(imgs)
    # create input txt for ffmpeg concat images as video
    filter_parts = []
    inputs = []
    for i, img in enumerate(imgs):
        inputs.append(f"-loop 1 -t {per:.2f} -i '{img}'")
    # voice and music inputs
    inputs_line = " ".join(inputs + [f"-i '{voice_file}'", f"-i '{bg_music}'", f"-i '{sfx_shutter}'", f"-i '{sfx_flash}'"])
    # build complex filter constructing video by overlaying images, apply zoom via scale crop
    # For reliability produce a basic slideshow with fade transitions using ffmpeg concat filter
    # create temporary file list for images via ffmpeg image2pipe not required. Simpler approach:
    # use ffmpeg to create video from images with zoom using zoompan is complicated.
    # Here we make a simple slideshow by converting each image to a short video then concat
    tmp_videos = []
    for idx, img in enumerate(imgs):
        tmp = f"/tmp/clip_{idx}.mp4"
        cmd = [
            "ffmpeg", "-y",
            "-loop", "1",
            "-i", img,
            "-vf", "scale=1080:1920,fade=t=in:st=0:d=0.5,fade=t=out:st={:.2f}:d=0.5".format(per-0.5),
            "-t", f"{per:.2f}",
            "-r", "30",
            "-c:v", "libx264",
            "-pix_fmt", "yuv420p",
            tmp
        ]
        subprocess.run(" ".join(cmd), shell=True, check=True)
        tmp_videos.append(tmp)
    # create file list
    listfile = "/tmp/list.txt"
    with open(listfile, "w", encoding="utf-8") as f:
        for t in tmp_videos:
            f.write(f"file '{t}'\n")
    # concat
    concat_tmp = "/tmp/concat.mp4"
    subprocess.run(f"ffmpeg -y -f concat -safe 0 -i {listfile} -c copy {concat_tmp}", shell=True, check=True)
    # mix audio: voice + bg music loop + sfx timed at start of each clip
    # For simplicity place sfx at the beginning of each clip sequentially
    # Build audio by overlay: loop bg to voice duration
    # get voice duration via ffprobe
    def get_duration(fpath):
        cmd = f"ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 '{fpath}'"
        out = subprocess.check_output(cmd, shell=True).decode().strip()
        return float(out)
    voice_dur = get_duration(voice_file)
    # loop bg to voice_dur
    bg_looped = "/tmp/bg_looped.mp3"
    subprocess.run(f"ffmpeg -y -stream_loop -1 -i '{bg_music}' -t {voice_dur} -c copy {bg_looped}", shell=True, check=True)
    # mix voice + bg so that voice is louder
    mixed = "/tmp/mixed_audio.mp3"
    subprocess.run(f"ffmpeg -y -i '{voice_file}' -i '{bg_looped}' -filter_complex \"[0:a]volume=1.0[a0];[1:a]volume=0.18[a1];[a0][a1]amix=inputs=2:duration=first:dropout_transition=2\" -c:a libmp3lame -q:a 4 {mixed}", shell=True, check=True)
    # final map: video + mixed audio
    subprocess.run(f"ffmpeg -y -i {concat_tmp} -i {mixed} -map 0:v -map 1:a -c:v libx264 -c:a aac -shortest -pix_fmt yuv420p -movflags +faststart {out_file}", shell=True, check=True)
    print("Built video:", out_file)

if __name__ == "__main__":
    images_dir = sys.argv[1]
    voice = sys.argv[2]
    sfx1 = sys.argv[3]
    sfx2 = sys.argv[4]
    bg = sys.argv[5]
    out = sys.argv[6] if len(sys.argv) > 6 else "final.mp4"
    build(images_dir, voice, sfx1, sfx2, bg, out)
