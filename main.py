# main.py
import os
import sys
import stat
import json
import time
import shutil
import zipfile
import tarfile
import platform
import tempfile
import threading
import subprocess
import urllib.request
from concurrent.futures import ThreadPoolExecutor
import tkinter as tk
from tkinter import filedialog
import eel

import io
# Prevent Bottle/Gevent from crashing when compiled with --noconsole
if sys.stdout is None:
    sys.stdout = io.StringIO()
if sys.stderr is None:
    sys.stderr = io.StringIO()

def resource_path(relative_path):
    """Checks PyInstaller's _internal (_MEIPASS) folder first, then exe folder."""
    if hasattr(sys, "_MEIPASS"):
        candidate = os.path.join(sys._MEIPASS, relative_path)
        if os.path.exists(candidate):
            return candidate
    if getattr(sys, "frozen", False):
        base_path = os.path.dirname(sys.executable)
    else:
        base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, relative_path)

IS_WINDOWS = platform.system() == "Windows"

APP_VERSION = "1.0.3"
# Replace with your actual GitHub username and repository name:
GITHUB_REPO = "SachinKJha/PulseTube"

# Setup OS-appropriate AppData directory so C:\Program Files never blocks writes
if IS_WINDOWS:
    APPDATA_DIR = os.path.join(os.environ.get("LOCALAPPDATA", os.path.expanduser("~")), "PulseTube")
    YTDLP_URL = "https://github.com/yt-dlp/yt-dlp/releases/latest/download/yt-dlp.exe"
    FFMPEG_ARCHIVE_URL = "https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-win64-gpl.zip"
    YTDLP_BIN_NAME = "yt-dlp.exe"
    FFMPEG_BIN_NAME = "ffmpeg.exe"
    FFPROBE_BIN_NAME = "ffprobe.exe"
else:
    APPDATA_DIR = os.path.join(os.path.expanduser("~"), ".local", "share", "pulsetube")
    YTDLP_URL = "https://github.com/yt-dlp/yt-dlp/releases/latest/download/yt-dlp"
    FFMPEG_ARCHIVE_URL = "https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-linux64-gpl.tar.xz"
    YTDLP_BIN_NAME = "yt-dlp"
    FFMPEG_BIN_NAME = "ffmpeg"
    FFPROBE_BIN_NAME = "ffprobe"

BIN_DIR = os.path.join(APPDATA_DIR, "bin")
TEMP_WORK_DIR = os.path.join(APPDATA_DIR, "temp_work")
os.makedirs(BIN_DIR, exist_ok=True)
os.makedirs(TEMP_WORK_DIR, exist_ok=True)

YTDLP_PATH = os.path.join(BIN_DIR, YTDLP_BIN_NAME)
FFMPEG_PATH = os.path.join(BIN_DIR, FFMPEG_BIN_NAME)
FFPROBE_PATH = os.path.join(BIN_DIR, FFPROBE_BIN_NAME)

# Global state for cancellation and active subprocesses
cancel_requested = False
active_processes = {}
process_lock = threading.Lock()

def resource_path(relative_path):
    """Finds bundled web assets whether inside _internal (_MEIPASS) or next to the .exe."""
    candidates = []
    if hasattr(sys, "_MEIPASS"):
        candidates.append(os.path.join(sys._MEIPASS, relative_path))
    if getattr(sys, "frozen", False):
        exe_dir = os.path.dirname(sys.executable)
        candidates.append(os.path.join(exe_dir, relative_path))
        candidates.append(os.path.join(exe_dir, "_internal", relative_path))
    candidates.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), relative_path))

    for path in candidates:
        if os.path.exists(path):
            return path
    return candidates[0]
eel.init(resource_path("web"))

def ui_log(message):
    try:
        eel.appendLog(message)()
    except Exception:
        pass

def get_startupinfo():
    if IS_WINDOWS:
        si = subprocess.STARTUPINFO()
        si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        return si
    return None

def make_executable(path):
    if not IS_WINDOWS and os.path.exists(path):
        st = os.stat(path)
        os.chmod(path, st.st_mode | stat.S_IEXEC)

def download_stream(url, dest, label):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req) as response:
        total_size = int(response.info().get("Content-Length", 0))
        downloaded = 0
        chunk_size = 262144  # Increased from 32KB to 256KB for much faster network writing
        with open(dest, "wb") as f:
            while True:
                chunk = response.read(chunk_size)
                if not chunk:
                    break
                f.write(chunk)
                downloaded += len(chunk)
                if total_size > 0:
                    pct = int((downloaded / total_size) * 100)
                    eel.updateDepProgress(f"{label} ({pct}%)", pct)()

@eel.expose
def init_dependencies():
    """Runs automatically when UI boots to verify or install yt-dlp and ffmpeg."""
    threading.Thread(target=_check_and_install_deps, daemon=True).start()

def _check_and_install_deps():
    try:
        # 1. Verify yt-dlp
        if not os.path.exists(YTDLP_PATH):
            ui_log("[SYSTEM] yt-dlp not found. Downloading latest binary...")
            eel.updateDepProgress("Starting yt-dlp download...", 0)()
            download_stream(YTDLP_URL, YTDLP_PATH, "Downloading yt-dlp")
            make_executable(YTDLP_PATH)
            ui_log("[SYSTEM] yt-dlp installed successfully.")

        # 2. Verify ffmpeg & ffprobe
        if not os.path.exists(FFMPEG_PATH) or not os.path.exists(FFPROBE_PATH):
            ui_log("[SYSTEM] FFmpeg/FFprobe missing. Downloading media suite...")
            
            # Force UI update before the heavy TLS handshake blocks the thread
            eel.updateDepProgress("Connecting to FFmpeg mirror (~100MB)...", 0)()
            
            ext = ".zip" if IS_WINDOWS else ".tar.xz"
            archive_path = os.path.join(TEMP_WORK_DIR, f"ffmpeg_pkg{ext}")
            download_stream(FFMPEG_ARCHIVE_URL, archive_path, "Downloading FFmpeg")

            # Force UI update before the CPU-heavy decompression locks the thread
            eel.updateDepProgress("Decompressing FFmpeg (This takes 30-60 seconds)...", 95)()
            ui_log("[SYSTEM] Extracting FFmpeg binaries...")
            extract_dir = os.path.join(TEMP_WORK_DIR, "ff_extract")
            os.makedirs(extract_dir, exist_ok=True)

            if IS_WINDOWS:
                with zipfile.ZipFile(archive_path, "r") as zf:
                    for member in zf.namelist():
                        if member.endswith("ffmpeg.exe"):
                            zf.extract(member, extract_dir)
                            shutil.move(os.path.join(extract_dir, member), FFMPEG_PATH)
                        elif member.endswith("ffprobe.exe"):
                            zf.extract(member, extract_dir)
                            shutil.move(os.path.join(extract_dir, member), FFPROBE_PATH)
            else:
                with tarfile.open(archive_path, "r:xz") as tf:
                    for member in tf.getmembers():
                        if member.name.endswith("/ffmpeg"):
                            member.name = "ffmpeg"
                            tf.extract(member, extract_dir)
                            shutil.move(os.path.join(extract_dir, "ffmpeg"), FFMPEG_PATH)
                        elif member.name.endswith("/ffprobe"):
                            member.name = "ffprobe"
                            tf.extract(member, extract_dir)
                            shutil.move(os.path.join(extract_dir, "ffprobe"), FFPROBE_PATH)

            shutil.rmtree(extract_dir, ignore_errors=True)
            if os.path.exists(archive_path):
                os.remove(archive_path)

            make_executable(FFMPEG_PATH)
            make_executable(FFPROBE_PATH)
            ui_log("[SYSTEM] FFmpeg & FFprobe ready.")

        eel.onDepsReady(BIN_DIR)()
        ui_log(f"[READY] Engine initialized in {BIN_DIR}")
    except Exception as e:
        ui_log(f"[ERROR] Dependency setup failed: {e}")
        eel.onDepError(str(e))()
        
@eel.expose
def browse_txt_file():
    root = tk.Tk()
    root.withdraw()
    root.attributes("-topmost", True)
    path = filedialog.askopenfilename(
        title="Select Links .txt File",
        filetypes=[("Text Files", "*.txt"), ("All Files", "*.*")]
    )
    root.destroy()
    return path

@eel.expose
def browse_output_folder():
    root = tk.Tk()
    root.withdraw()
    root.attributes("-topmost", True)
    path = filedialog.askdirectory(title="Select Download Destination Folder")
    root.destroy()
    return path

@eel.expose
def parse_txt_and_fetch_metadata(txt_path):
    """Reads links from the .txt file and launches parallel metadata pre-fetchers."""
    if not txt_path or not os.path.exists(txt_path):
        return {"error": "Selected .txt file does not exist."}

    with open(txt_path, "r", encoding="utf-8", errors="ignore") as f:
        raw_lines = [line.strip() for line in f if line.strip() and not line.strip().startswith("#")]

    if not raw_lines:
        return {"error": "No valid links found in the selected .txt file."}

    items = []
    for idx, url in enumerate(raw_lines):
        items.append({
            "id": idx,
            "url": url,
            "title": f"Fetching metadata... ({url[:42]}...)",
            "channel": "Loading...",
            "duration_str": "--:--",
            "thumbnail": "",
            "loaded": False
        })

    # Spawn background pool to fetch metadata concurrently (6 at a time for speed)
    threading.Thread(target=_batch_fetch_metadata, args=(items,), daemon=True).start()
    return {"items": items}

def _format_duration(seconds):
    if not seconds:
        return "Live / Unknown"
    try:
        seconds = int(float(seconds))
        h = seconds // 3600
        m = (seconds % 3600) // 60
        s = seconds % 60
        return f"{h:02d}:{m:02d}:{s:02d}" if h > 0 else f"{m:02d}:{s:02d}"
    except Exception:
        return "--:--"

def _fetch_single_meta(item):
    url = item["url"]
    idx = item["id"]
    cmd = [
        YTDLP_PATH,
        "--dump-json",
        "--no-playlist",
        "--skip-download",
        "--no-warnings",
        url
    ]
    try:
        res = subprocess.run(
            cmd,
            startupinfo=get_startupinfo(),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=25
        )
        if res.returncode == 0 and res.stdout.strip():
            first_line = res.stdout.strip().splitlines()[0]
            data = json.loads(first_line)
            meta = {
                "id": idx,
                "title": data.get("title") or url,
                "channel": data.get("uploader") or data.get("channel") or "YouTube Media",
                "duration_str": _format_duration(data.get("duration")),
                "thumbnail": data.get("thumbnail") or "",
                "loaded": True,
                "error": False
            }
            eel.updateItemMetadata(meta)()
            ui_log(f"[META] Loaded: {meta['title']}")
            return
    except Exception as e:
        ui_log(f"[WARN] Metadata timeout/error for link #{idx + 1}: {e}")

    # Fallback if metadata fetch fails so user can still attempt download
    fallback = {
        "id": idx,
        "title": f"Media Stream #{idx + 1} ({url})",
        "channel": "Direct Link",
        "duration_str": "Full Length",
        "thumbnail": "",
        "loaded": True,
        "error": False
    }
    eel.updateItemMetadata(fallback)()

def _batch_fetch_metadata(items):
    ui_log(f"[SYSTEM] Pre-fetching metadata for {len(items)} link(s) using 6 parallel workers...")
    with ThreadPoolExecutor(max_workers=6) as executor:
        executor.map(_fetch_single_meta, items)
    ui_log("[SYSTEM] Metadata pre-fetch complete.")
    eel.onMetadataBatchComplete()()

@eel.expose
def start_download_queue(payload):
    """
    payload = {
        'out_dir': str,
        'format_type': 'mp3' | 'mp4',
        'quality': str,
        'concurrency': int,
        'items': [
            {
                'id': int,
                'url': str,
                'title': str,
                'use_trim': bool,
                'trim_from': str,
                'trim_to': str
            }
        ]
    }
    """
    global cancel_requested
    cancel_requested = False
    threading.Thread(target=_run_download_manager, args=(payload,), daemon=True).start()

@eel.expose
def cancel_all_downloads():
    global cancel_requested
    cancel_requested = True
    ui_log("[WARN] Cancel signal received! Terminating active processes...")
    with process_lock:
        for pid, proc in list(active_processes.items()):
            try:
                proc.terminate()
            except Exception:
                pass

def _download_worker(task, out_dir, format_type, quality):
    global cancel_requested
    item_id = task["id"]
    url = task["url"]
    use_trim = task.get("use_trim", False)
    trim_from = (task.get("trim_from") or "").strip()
    trim_to = (task.get("trim_to") or "").strip()

    if cancel_requested:
        eel.updateItemStatus(item_id, "Cancelled", 0, "", "cancelled")()
        return False

    # Dedicated isolated temp folder for this item inside AppData
    item_temp_dir = os.path.join(TEMP_WORK_DIR, f"job_{item_id}_{int(time.time()*1000)}")
    os.makedirs(item_temp_dir, exist_ok=True)

    max_retries = 3
    for attempt in range(1, max_retries + 1):
        if cancel_requested:
            shutil.rmtree(item_temp_dir, ignore_errors=True)
            eel.updateItemStatus(item_id, "Cancelled", 0, "", "cancelled")()
            return False

        # Clean any partial files from previous retry
        for f in os.listdir(item_temp_dir):
            try:
                os.remove(os.path.join(item_temp_dir, f))
            except Exception:
                pass

        status_label = "Downloading..." if attempt == 1 else f"Retrying ({attempt}/{max_retries})..."
        eel.updateItemStatus(item_id, status_label, 2, "Starting...", "downloading")()

        cmd = [
            YTDLP_PATH,
            "--ffmpeg-location", BIN_DIR,
            "--no-playlist",
            "--newline",
            "--progress-template", "download:[PB]%(progress._percent_str)s|%(progress._speed_str)s|%(progress._eta_str)s",
            "--embed-metadata",
        ]

        if format_type == "mp3":
            # Map quality selection: '0' (Best/320K), '192K', '128K'
            audio_q = "0" if quality == "320" else f"{quality}K"
            cmd.extend([
                "-x",
                "--audio-format", "mp3",
                "--audio-quality", audio_q,
                "--embed-thumbnail",
                "--convert-thumbnails", "jpg"
            ])
            target_ext = ".mp3"
        else:
            # MP4 Video: Prefer H.264 (avc1) + m4a to prevent AV1 green-bar decoder glitches
            res_map = {
                "2160": "bestvideo[height<=2160][vcodec^=avc1]+bestaudio[ext=m4a]/bestvideo[height<=2160][vcodec^=vp9]+bestaudio[ext=m4a]/bestvideo[height<=2160]+bestaudio/best[height<=2160]/best",
                "1440": "bestvideo[height<=1440][vcodec^=avc1]+bestaudio[ext=m4a]/bestvideo[height<=1440][vcodec^=vp9]+bestaudio[ext=m4a]/bestvideo[height<=1440]+bestaudio/best[height<=1440]/best",
                "1080": "bestvideo[height<=1080][vcodec^=avc1]+bestaudio[ext=m4a]/bestvideo[height<=1080]+bestaudio/best[height<=1080]/best",
                "720": "bestvideo[height<=720][vcodec^=avc1]+bestaudio[ext=m4a]/bestvideo[height<=720]+bestaudio/best[height<=720]/best",
                "480": "bestvideo[height<=480][vcodec^=avc1]+bestaudio[ext=m4a]/bestvideo[height<=480]+bestaudio/best[height<=480]/best",
            }
            fmt_str = res_map.get(str(quality), res_map["1080"])
            cmd.extend([
                "-f", fmt_str,
                "--merge-output-format", "mp4",
                "--embed-thumbnail"
            ])
            target_ext = ".mp4"

        # Timestamp trimming if enabled by user for this video
        if use_trim and (trim_from or trim_to):
            start_t = trim_from if trim_from else "00:00"
            end_t = trim_to if trim_to else "inf"
            cmd.extend([
                "--download-sections", f"*{start_t}-{end_t}",
                "--force-keyframes-at-cuts"
            ])
            ui_log(f"[TRIM] Item #{item_id + 1}: Custom section *{start_t}-{end_t}")

        cmd.extend([
            "-o", os.path.join(item_temp_dir, "%(title)s.%(ext)s"),
            url
        ])

        try:
            proc = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding="utf-8",
                errors="replace",
                startupinfo=get_startupinfo()
            )
            with process_lock:
                active_processes[item_id] = proc

            last_err_line = ""
            for line in proc.stdout:
                if cancel_requested:
                    proc.terminate()
                    break
                clean = line.strip()
                if not clean:
                    continue
                if clean.startswith("[PB]"):
                    parts = clean.replace("[PB]", "").split("|")
                    if len(parts) >= 3:
                        pct_raw = parts[0].strip().replace("%", "")
                        speed_raw = parts[1].strip()
                        eta_raw = parts[2].strip()
                        try:
                            pct_val = float(pct_raw)
                        except ValueError:
                            pct_val = 0.0
                        meta_str = f"{speed_raw} • ETA {eta_raw}"
                        eel.updateItemStatus(item_id, status_label, pct_val, meta_str, "downloading")()
                elif "[ExtractAudio]" in clean or "[Merger]" in clean or "[Metadata]" in clean or "[ThumbnailsConvertor]" in clean:
                    eel.updateItemStatus(item_id, "Processing & Tagging...", 98, "FFmpeg", "processing")()
                else:
                    if "ERROR:" in clean:
                        last_err_line = clean
                    ui_log(f"[#{item_id + 1}] {clean}")

            proc.wait()
            with process_lock:
                active_processes.pop(item_id, None)

            if cancel_requested:
                shutil.rmtree(item_temp_dir, ignore_errors=True)
                eel.updateItemStatus(item_id, "Cancelled", 0, "", "cancelled")()
                return False

            if proc.returncode == 0:
                # Move final file(s) to destination with clean (1), (2) duplicate handling
                moved_any = False
                for fname in os.listdir(item_temp_dir):
                    if fname.endswith(target_ext):
                        base, ext = os.path.splitext(fname)
                        final_name = fname
                        counter = 1
                        while os.path.exists(os.path.join(out_dir, final_name)):
                            final_name = f"{base} ({counter}){ext}"
                            counter += 1
                        shutil.move(
                            os.path.join(item_temp_dir, fname),
                            os.path.join(out_dir, final_name)
                        )
                        moved_any = True
                        ui_log(f"[DONE] Saved: {final_name}")

                if moved_any:
                    shutil.rmtree(item_temp_dir, ignore_errors=True)
                    eel.updateItemStatus(item_id, "Completed", 100, "Saved", "done")()
                    return True
                else:
                    last_err_line = "Output file was not generated."

            ui_log(f"[WARN] Item #{item_id + 1} attempt {attempt} failed: {last_err_line}")
        except Exception as e:
            ui_log(f"[ERROR] Worker exception on item #{item_id + 1}: {e}")

        if attempt < max_retries and not cancel_requested:
            for wait_sec in range(4, 0, -1):
                if cancel_requested:
                    break
                eel.updateItemStatus(item_id, f"Retry in {wait_sec}s ({attempt}/{max_retries})", 0, "Waiting...", "retry")()
                time.sleep(1)

    shutil.rmtree(item_temp_dir, ignore_errors=True)
    eel.updateItemStatus(item_id, "Failed after 3 attempts", 100, "Error", "error")()
    return False

def _run_download_manager(payload):
    out_dir = payload.get("out_dir", "")
    format_type = payload.get("format_type", "mp3")
    quality = payload.get("quality", "320")
    concurrency = int(payload.get("concurrency", 3))
    items = payload.get("items", [])

    total = len(items)
    completed = 0
    succeeded = 0
    lock = threading.Lock()

    os.makedirs(out_dir, exist_ok=True)
    ui_log(f"[QUEUE] Starting batch of {total} item(s) | Format: {format_type.upper()} | Workers: {concurrency}")
    eel.updateMasterProgress(0, total, f"Downloading 0 of {total} completed...")()

    def wrapped_worker(task):
        nonlocal completed, succeeded
        ok = _download_worker(task, out_dir, format_type, quality)
        with lock:
            completed += 1
            if ok:
                succeeded += 1
            eel.updateMasterProgress(completed, total, f"Progress: {completed} of {total} processed ({succeeded} succeeded)")()

    with ThreadPoolExecutor(max_workers=concurrency) as pool:
        pool.map(wrapped_worker, items)

    if cancel_requested:
        eel.onQueueFinished(succeeded, total, True)()
        ui_log(f"[QUEUE] Cancelled by user. ({succeeded}/{total} completed before stop).")
    else:
        eel.onQueueFinished(succeeded, total, False)()
        ui_log(f"[QUEUE] Batch finished! {succeeded}/{total} downloaded successfully.")

def find_chromium_browser():
    if IS_WINDOWS:
        candidates = [
            os.path.expandvars(r"%ProgramFiles%\Google\Chrome\Application\chrome.exe"),
            os.path.expandvars(r"%ProgramFiles(x86)%\Google\Chrome\Application\chrome.exe"),
            os.path.expandvars(r"%LocalAppData%\Google\Chrome\Application\chrome.exe"),
            os.path.expandvars(r"%ProgramFiles(x86)%\Microsoft\Edge\Application\msedge.exe"),
            os.path.expandvars(r"%ProgramFiles%\Microsoft\Edge\Application\msedge.exe"),
        ]
        for path in candidates:
            if os.path.exists(path):
                return path
    else:
        for bin_name in ["google-chrome", "google-chrome-stable", "chromium", "chromium-browser", "brave-browser", "microsoft-edge"]:
            found = shutil.which(bin_name)
            if found:
                return found
    return None


def _parse_version(v_str):
    """Converts 'v1.0.2' into a comparable tuple (1, 0, 2)."""
    clean = v_str.strip().lstrip("vV")
    parts = []
    for p in clean.split("."):
        num = "".join(ch for ch in p if ch.isdigit())
        parts.append(int(num) if num else 0)
    return tuple(parts)

@eel.expose
def check_for_updates():
    """Checks GitHub Releases in the background on startup."""
    threading.Thread(target=_check_github_release, daemon=True).start()

def _check_github_release():
    ui_log(f"[UPDATE] Checking {GITHUB_REPO} (Current: v{APP_VERSION})...")
    api_url = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"
    try:
        req = urllib.request.Request(
            api_url,
            headers={
                "User-Agent": "PulseTube-Updater",
                "Accept": "application/vnd.github.v3+json"
            }
        )
        with urllib.request.urlopen(req, timeout=8) as resp:
            data = json.loads(resp.read().decode("utf-8"))

        latest_tag = data.get("tag_name", "")
        if not latest_tag:
            return

        if _parse_version(latest_tag) > _parse_version(APP_VERSION):
            notes = data.get("body") or "Bug fixes and performance improvements."
            assets = data.get("assets", [])
            target_ext = ".exe" if IS_WINDOWS else ".deb"
            download_url = ""

            for asset in assets:
                name = asset.get("name", "").lower()
                if name.endswith(target_ext):
                    download_url = asset.get("browser_download_url", "")
                    break

            if download_url:
                ui_log(f"[UPDATE] New version {latest_tag} found on GitHub!")
                eel.showUpdateModal(latest_tag, notes, download_url)()
            else:
                ui_log(f"[UPDATE] Version {latest_tag} found, but no {target_ext} installer attached.")
        else:
            ui_log(f"[UPDATE] App is up to date (v{APP_VERSION}).")
    except Exception as e:
        ui_log(f"[UPDATE] Update check skipped: {e}")


@eel.expose
def start_self_update(download_url):
    """Downloads the new installer from GitHub and executes it."""
    threading.Thread(target=_run_self_update, args=(download_url,), daemon=True).start()

IS_UPDATING = False

def _run_self_update(download_url):
    global IS_UPDATING
    try:
        ext = ".exe" if IS_WINDOWS else ".deb"
        installer_path = os.path.join(TEMP_WORK_DIR, f"PulseTube_Update{ext}")
        if os.path.exists(installer_path):
            os.remove(installer_path)

        req = urllib.request.Request(download_url, headers={"User-Agent": "PulseTube-Updater"})
        with urllib.request.urlopen(req, timeout=30) as response:
            total_size = int(response.info().get("Content-Length", 0))
            downloaded = 0
            chunk_size = 262144
            with open(installer_path, "wb") as f:
                while True:
                    chunk = response.read(chunk_size)
                    if not chunk:
                        break
                    f.write(chunk)
                    downloaded += len(chunk)
                    if total_size > 0:
                        pct = int((downloaded / total_size) * 100)
                        eel.updateSelfUpdateProgress(f"Downloading update ({pct}%)...", pct)()
                    if total_size > 0 and downloaded < total_size:
                        raise RuntimeError("Download interrupted. Please check your internet connection and try again.")

        eel.updateSelfUpdateProgress("Installing update & restarting...", 100)()
        IS_UPDATING = True
        time.sleep(0.5)

        if IS_WINDOWS:
            # Spawn the detached update script BEFORE closing the window or exiting
            current_exe = os.path.abspath(sys.executable)
            bat_path = os.path.join(TEMP_WORK_DIR, "apply_update.bat")
            with open(bat_path, "w", encoding="utf-8") as bf:
                bf.write("@echo off\r\n")
                # Wait ~3 seconds for the old PulseTube.exe to fully exit (works without console stdin)
                bf.write("ping 127.0.0.1 -n 4 >nul\r\n")
                # Run Inno Setup silently and WAIT for it to finish overwriting files
                bf.write(f'start /wait "" "{installer_path}" /VERYSILENT /SUPPRESSMSGBOXES /NORESTART /CLOSEAPPLICATIONS\r\n')
                # Relaunch the newly updated PulseTube.exe
                bf.write(f'start "" "{current_exe}"\r\n')
                # Clean up temporary installer and batch script
                bf.write(f'del /f /q "{installer_path}" >nul 2>&1\r\n')
                bf.write('del /f /q "%~f0" >nul 2>&1\r\n')

            CREATE_NO_WINDOW = 0x08000000
            subprocess.Popen(
                ["cmd.exe", "/c", bat_path],
                creationflags=CREATE_NO_WINDOW,
                close_fds=True
            )
        else:
            # On Linux, wait 2s, prompt for sudo via polkit GUI (pkexec) to install .deb, then relaunch
            cmd = f'sleep 2 && pkexec dpkg -i "{installer_path}" && rm -f "{installer_path}" && /opt/pulsetube/PulseTube &'
            subprocess.Popen(["bash", "-c", cmd], start_new_session=True)

        # Now safely close the Chrome app window and exit the old process
        try:
            eel.closeWindowForUpdate()()
        except Exception:
            pass
        time.sleep(0.3)
        os._exit(0)

    except Exception as e:
        IS_UPDATING = False
        ui_log(f"[ERROR] Update failed: {e}")
        eel.onSelfUpdateError(str(e))()

                
def launch_app():
    browser_path = find_chromium_browser()
    if browser_path:
        eel.browsers.set_path("chrome", browser_path)

    # Dedicated profile directory prevents Chrome's "Who's using Chrome?" account popup
    browser_profile_dir = os.path.join(APPDATA_DIR, "browser_profile")
    os.makedirs(browser_profile_dir, exist_ok=True)

    def on_close(page, sockets):
        if not sockets and not IS_UPDATING:
            os._exit(0)

    eel.start(
        "index.html",
        mode="chrome",
        host="127.0.0.1",
        port=0,
        size=(1120, 780),
        close_callback=on_close,
        cmdline_args=[
            f"--user-data-dir={browser_profile_dir}",
            "--disk-cache-size=1",
            "--no-first-run",
            "--no-default-browser-check",
            "--disable-extensions"
        ]
    )

if __name__ == "__main__":
    launch_app()