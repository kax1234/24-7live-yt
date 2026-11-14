import os
import shlex
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
VIDEO_DIR = ROOT / "assets" / "backgrounds"
MUSIC_DIR = ROOT / "assets" / "music"
VIDEO_EXTS = {".mp4", ".mkv", ".mov", ".webm"}
AUDIO_EXTS = {".mp3", ".m4a", ".aac", ".wav", ".ogg"}

def main():
    key = os.environ.get("YT_STREAM_KEY", "").strip()
    if not key:
        raise SystemExit("Missing required GitHub Actions secret: YT_STREAM_KEY")

    videos = sorted(p for p in VIDEO_DIR.iterdir() if p.is_file() and p.suffix.lower() in VIDEO_EXTS)
    tracks = sorted(p for p in MUSIC_DIR.iterdir() if p.is_file() and p.suffix.lower() in AUDIO_EXTS)
    if not videos:
        raise SystemExit(f"No video found in {VIDEO_DIR}")
    if not tracks:
        raise SystemExit(f"No music files found in {MUSIC_DIR}")

    # Use the first available background for now; additional backgrounds can be added later.
    video = videos[0]
    with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False, encoding="utf-8") as playlist:
        playlist_path = playlist.name
        # Repeat the ordered playlist many times instead of seeking/looping
        # the concat demuxer, avoiding seek errors during long live sessions.
        for _ in range(500):
            for track in tracks:
                safe_path = str(track.resolve()).replace("'", "'\\''")
                playlist.write(f"file '{safe_path}'\n")

    print(f"Background: {video.name}", flush=True)
    print("Playlist:", flush=True)
    for track in tracks:
        print(f" - {track.name}", flush=True)

    command = [
        "ffmpeg", "-hide_banner", "-loglevel", "info",
        "-stream_loop", "-1", "-re", "-i", str(video),
        "-re", "-f", "concat", "-safe", "0", "-i", playlist_path,
        "-map", "0:v:0", "-map", "1:a:0",
        "-vf", "scale=1280:720:force_original_aspect_ratio=decrease,pad=1280:720:(ow-iw)/2:(oh-ih)/2,format=yuv420p",
        "-r", "30", "-c:v", "libx264", "-preset", "veryfast",
        "-b:v", "2500k", "-maxrate", "2500k", "-bufsize", "5000k",
        "-g", "60", "-keyint_min", "60", "-sc_threshold", "0",
        "-c:a", "aac", "-b:a", "128k", "-ar", "44100",
        "-f", "flv", f"rtmp://a.rtmp.youtube.com/live2/{key}"
    ]
    try:
        subprocess.run(command, check=True)
    finally:
        try:
            os.unlink(playlist_path)
        except OSError:
            pass

if __name__ == "__main__":
    main()
