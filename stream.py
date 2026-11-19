import os
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
VIDEO_DIR = ROOT / "assets" / "backgrounds"
MUSIC_DIR = ROOT / "assets" / "music"
BIRTHDAY_IMAGE = VIDEO_DIR / "birthday.png"
VIDEO_EXTS = {".mp4", ".mkv", ".mov", ".webm"}
AUDIO_EXTS = {".mp3", ".m4a", ".aac", ".wav", ".ogg"}

def main():
    key = os.environ.get("YT_STREAM_KEY", "").strip()
    if not key:
        raise SystemExit("Missing required GitHub Actions secret: YT_STREAM_KEY")

    videos = sorted(
        p for p in VIDEO_DIR.iterdir()
        if p.is_file() and p.suffix.lower() in VIDEO_EXTS
    )
    tracks = sorted(
        p for p in MUSIC_DIR.iterdir()
        if p.is_file() and p.suffix.lower() in AUDIO_EXTS
    )
    if not videos:
        raise SystemExit(f"No normal background video found in {VIDEO_DIR}")
    if not BIRTHDAY_IMAGE.is_file():
        raise SystemExit(f"Birthday image missing: {BIRTHDAY_IMAGE}")
    if not tracks:
        raise SystemExit(f"No music files found in {MUSIC_DIR}")

    normal_video = videos[0]
    with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False, encoding="utf-8") as playlist:
        playlist_path = playlist.name
        for _ in range(500):
            for track in tracks:
                safe_path = str(track.resolve()).replace("'", "'\\''")
                playlist.write(f"file '{safe_path}'\n")

    print(f"Normal background: {normal_video.name}", flush=True)
    print(f"Birthday background: {BIRTHDAY_IMAGE.name}", flush=True)
    print("Chat commands: !birthday (birthday screen), !normal (regular screen)", flush=True)
    print("Music playlist:", flush=True)
    for track in tracks:
        print(f" - {track.name}", flush=True)

    # Both video sources stay open. streamselect changes only the video path;
    # the audio concat input and encoder remain uninterrupted.
    filter_graph = (
        "[0:v]scale=1280:720:force_original_aspect_ratio=decrease,"
        "pad=1280:720:(ow-iw)/2:(oh-ih)/2,fps=30,setsar=1,format=yuv420p[normal];"
        "[1:v]scale=1280:720:force_original_aspect_ratio=decrease,"
        "pad=1280:720:(ow-iw)/2:(oh-ih)/2,fps=30,setsar=1,format=yuv420p[birthday];"
        "[normal][birthday]streamselect@birthday_bg=inputs=2:map=0,"
        "zmq=bind_address=tcp\://127.0.0.1\:5555[outv]"
    )

    command = [
        "ffmpeg", "-hide_banner", "-loglevel", "info",
        "-thread_queue_size", "512", "-stream_loop", "-1", "-re", "-i", str(normal_video),
        "-thread_queue_size", "512", "-loop", "1", "-framerate", "30", "-re", "-i", str(BIRTHDAY_IMAGE),
        "-thread_queue_size", "512", "-re", "-f", "concat", "-safe", "0", "-i", playlist_path,
        "-filter_complex", filter_graph,
        "-map", "[outv]", "-map", "2:a:0",
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
