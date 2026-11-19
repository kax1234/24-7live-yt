import json
import os
import queue
import subprocess
import threading
import time
import urllib.error
import urllib.request

import zmq

BASE_URL = os.environ.get("ANALYTICS_URL", "").rstrip("/")
TOKEN = os.environ.get("ANALYTICS_INGEST_TOKEN", "").strip()
VIDEO_ID = os.environ.get("YT_VIDEO_ID", "").strip()
ZMQ_ENDPOINT = "tcp://127.0.0.1:5555"
events = queue.Queue(maxsize=3000)
stop = threading.Event()


def switch_background(command):
    """Send a live video-only switch to FFmpeg; audio is not restarted."""
    try:
        context = zmq.Context.instance()
        socket = context.socket(zmq.REQ)
        socket.setsockopt(zmq.LINGER, 0)
        socket.setsockopt(zmq.RCVTIMEO, 2000)
        socket.setsockopt(zmq.SNDTIMEO, 2000)
        socket.connect(ZMQ_ENDPOINT)
        target = "1" if command == "!birthday" else "0"
        socket.send_string(f"streamselect@birthday_bg map {target}")
        reply = socket.recv_string()
        socket.close()
        print(f"[BACKGROUND] {command} sent to FFmpeg; response: {reply}", flush=True)
    except Exception as exc:
        print(f"[BACKGROUND] Could not switch for {command}: {type(exc).__name__}: {exc}", flush=True)


def chat_reader():
    if not VIDEO_ID:
        print("[ANALYTICS] Disabled: missing YT_VIDEO_ID.", flush=True)
        return
    proc = subprocess.Popen(
        ["node", "chat_reader.js"],
        stdout=subprocess.PIPE,
        stderr=None,
        text=True,
        bufsize=1,
        env=os.environ.copy(),
    )
    try:
        for line in proc.stdout:
            if stop.is_set():
                break
            try:
                item = json.loads(line)
                if item.get("author_id") and item.get("author"):
                    item["text"] = str(item.get("text") or "")[:300]
                    command = item["text"].strip().lower()
                    if command in ("!birthday", "!normal"):
                        switch_background(command)
                    try:
                        events.put_nowait(item)
                    except queue.Full:
                        print("[ANALYTICS] Queue full; dropping event.", flush=True)
            except json.JSONDecodeError:
                continue
        code = proc.wait()
        if code:
            print(f"[ANALYTICS] Chat reader exited with code {code}.", flush=True)
    finally:
        if proc.poll() is None:
            proc.terminate()
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                proc.kill()


def sender():
    endpoint = BASE_URL + "/api/ingest"
    headers = {
        "Authorization": "Bearer " + TOKEN,
        "Content-Type": "application/json",
        "Accept": "application/json",
        "User-Agent": "KAXMOK-Analytics/1.0",
    }
    while not stop.is_set() or not events.empty():
        try:
            batch = [events.get(timeout=1)]
        except queue.Empty:
            continue
        deadline = time.monotonic() + 0.5
        while len(batch) < 20 and time.monotonic() < deadline:
            try:
                batch.append(events.get_nowait())
            except queue.Empty:
                time.sleep(0.05)
        payload = json.dumps({"messages": batch}).encode("utf-8")
        sent = False
        for attempt in range(3):
            try:
                req = urllib.request.Request(endpoint, data=payload, headers=headers, method="POST")
                with urllib.request.urlopen(req, timeout=15) as response:
                    result = json.loads(response.read().decode("utf-8", errors="replace"))
                    if response.status == 200 and result.get("ok"):
                        print(f"[ANALYTICS] SUCCESS: {result.get('accepted', len(batch))} chat events uploaded; {len(result.get('replies', []))} command replies returned.", flush=True)
                        sent = True
                        break
                    print("[ANALYTICS] Worker rejected batch:", str(result)[:300], flush=True)
            except urllib.error.HTTPError as exc:
                print(f"[ANALYTICS] HTTP {exc.code}: {exc.read(300).decode('utf-8', errors='replace')}", flush=True)
            except Exception as exc:
                print(f"[ANALYTICS] Attempt {attempt + 1}/3 failed: {type(exc).__name__}: {exc}", flush=True)
            time.sleep(2 * (attempt + 1))
        if not sent:
            print(f"[ANALYTICS] FAILED: dropped {len(batch)} events after retries.", flush=True)


def main():
    if not BASE_URL or not TOKEN:
        raise SystemExit("Missing ANALYTICS_URL or ANALYTICS_INGEST_TOKEN.")
    reader = threading.Thread(target=chat_reader, name="youtube-chat-reader", daemon=True)
    worker = threading.Thread(target=sender, name="analytics-sender", daemon=True)
    reader.start()
    worker.start()
    try:
        while reader.is_alive():
            reader.join(timeout=1)
    except KeyboardInterrupt:
        pass
    finally:
        stop.set()
        worker.join(timeout=20)


if __name__ == "__main__":
    main()
