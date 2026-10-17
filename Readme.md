<div align="center">

  <img src="web/icon.png" alt="PulseTube Studio Logo" width="128" height="128" style="border-radius: 28px; box-shadow: 0 10px 30px rgba(255, 0, 51, 0.3);" />

  # PulseTube Studio
  **A high-performance batch media downloader with frosted-glass aesthetics & precision timestamp trimming.**

  [![GitHub Release](https://img.shields.io/github/v/release/SachinKJha/PulseTube?style=for-the-badge&color=FF0033&logo=github)](https://github.com/SachinKJha/PulseTube/releases/latest)
  [![Platform](https://img.shields.io/badge/Platform-Windows%2010%2B%20%7C%20Linux%20x64-blue?style=for-the-badge&logo=linux&logoColor=white)](https://github.com/SachinKJha/PulseTube/releases/latest)
  [![Engine](https://img.shields.io/badge/Engine-yt--dlp%20%2B%20FFmpeg-red?style=for-the-badge)](https://github.com/yt-dlp/yt-dlp)
  [![License](https://img.shields.io/badge/License-MIT-emerald?style=for-the-badge)](LICENSE)

  <p align="center">
    <a href="#-quick-downloads">Direct Downloads</a> •
    <a href="#-key-features">Key Features</a> •
    <a href="#-how-it-works">How It Works</a> •
    <a href="#-architecture">Architecture</a> •
    <a href="#-building-from-source">Build from Source</a>
  </p>

  <img src="https://raw.githubusercontent.com/SachinKJha/PulseTube/main/web/assets/preview.png" alt="PulseTube Studio Interface" width="900" style="border-radius: 14px; border: 1px solid rgba(255,255,255,0.1); box-shadow: 0 25px 50px rgba(0,0,0,0.5);" />

</div>

---

## ⚡ Overview

**PulseTube Studio** bridges the complete flexibility of `yt-dlp` and `FFmpeg` with a modern YouTube-inspired dark obsidian frosted-glass interface. 

Built for archivists, researchers, creators, and audiophiles, it eliminates command-line friction while introducing features absent in most desktop wrappers:
- **Per-item custom timestamp trimming** within batch queues.
- **Multi-worker concurrent pipelines** with independent progress, ETA, and throughput monitors.
- **True 4K VP9 & 1080p H.264 stream selection** to eliminate green artifact lines on hardware decoders.
- **Over-the-air (OTA) updates** powered by GitHub Releases.

---

## 📦 Quick Downloads

| Operating System | Package Type | Link |
| :--- | :--- | :--- |
| **Windows 10 / 11** | Modern Inno Setup Installer (`.exe`) | [Download `PulseTube_Setup.exe`](https://github.com/SachinKJha/PulseTube/releases/latest) |
| **Linux (Ubuntu / Mint / Debian)** | Native Debian Binary (`.deb`) | [Download `pulsetube_amd64.deb`](https://github.com/SachinKJha/PulseTube/releases/latest) |
| **Windows (Portable)** | Standalone Archive (`.zip`) | [Download `PulseTube_Portable.zip`](https://github.com/SachinKJha/PulseTube/releases/latest) |

---

## ✨ Key Features

- **🎯 Precision Timestamp Trimming:** Expand any card in your queue and define `From: [MM:SS]` and `To: [MM:SS]` points. The engine uses keyframe-accurate cuts without redownloading the entire stream.
- **⚡ 4-Worker Concurrency Engine:** Download up to 4 streams concurrently with independent progress, ETA, and transfer speed monitors.
- **🎨 Frosted Glass UI:** Built using hardware-accelerated CSS backdrop filters, responsive dark/light modes, ambient red glow depth, and smooth animated state drawers.
- **🎧 Studio Audio Extraction:** Extract audio up to **320 kbps MP3** with automatic high-resolution cover art embedding and ID3 tagging.
- **🎬 Glitch-Free 4K / 2K & 1080p Video:** Smart codec fallback routes 1080p to native H.264 (`avc1`) for universal player compatibility and dynamically promotes 2K/4K to VP9—preventing Windows hardware decoder green-bar glitches.
- **📁 Flexible Link Input:** 
  - Drag and drop `.txt` link files directly onto the app window.
  - Paste single links or comma-separated lists (`link1, link2, link3`).
  - Automatically unfolds YouTube Playlists and Mixes into individually selectable items.
- **🔄 Zero-Friction OTA Updates:** Automated background checks against GitHub Releases. Updates download in seconds, self-terminate the old instance, and seamlessly relaunch.
- **🛡️ Sandbox & Self-Healing:** Stores runtime binaries (`yt-dlp`, `FFmpeg`) in isolated user-space directories (`%LOCALAPPDATA%` on Windows, `~/.local/share` on Linux), preventing OneDrive locks and write-permission crashes.

---

## 🚀 Quickstart Guide

### 1. Load Your Links
- **Method A:** Click **Browse .txt** or drag & drop a `.txt` file containing YouTube URLs into the drop target.
- **Method B:** Paste URLs into the link bar separated by commas:
  ```text
  https://youtu.be/dQw4w9WgXcQ, https://youtu.be/9bZkp7q19f0
  ```

### 2. Configure Formats & Ranges
- Toggle between **MP3 Audio** (128 / 192 / 320 kbps) and **MP4 Video** (480p to 4K Ultra HD).
- Click the chevron (▾) on any video item to expand its trim panel:
  - Check **Download custom timestamp section only**.
  - Specify start and end times (e.g., `00:45` to `02:30`).

### 3. Choose Destination & Run
- Click **Browse Dest** to pick your save folder.
- Select your concurrency level (1x Sequential to 4x Turbo).
- Hit **Download Selected** and watch individual per-task progress meters.

---

## 🛠️ Architecture

```
PulseTube Studio
├── Frontend (Chromium / Edge App Mode)
│   ├── Tailwind CSS Glassmorphism Engine
│   ├── Inter & JetBrains Mono Typography
│   └── Bi-directional Eel IPC Bridge
└── Backend (Python 3 Engine)
    ├── Asynchronous Metadata Scraper (oEmbed + yt-dlp JSON)
    ├── ThreadPoolExecutor Queue (1–4 Parallel Workers)
    ├── Subprocess Wrapper (yt-dlp + FFmpeg stream parsing)
    └── GitHub REST API Auto-Updater Loop
```

---

## 💻 Building from Source

### Prerequisites
- Python 3.10+
- Linux (for cross-compiling both `.deb` and `.exe`) or Windows
- Inno Setup 6 (for packaging Windows setup executables)
- Wine (if building Windows targets from Linux)

### 1. Clone & Set Up Virtual Environment
```bash
git clone https://github.com/SachinKJha/PulseTube.git
cd PulseTube

python3 -m venv venv
source venv/bin/activate  # On Windows: .\venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Run Locally in Development Mode
```bash
python3 main.py
```

### 3. Compile Binary Packages
```bash
# Compile Linux .deb
chmod +x build_linux_deb.sh
./build_linux_deb.sh

# Ship new update to GitHub (Builds Windows + Linux, pushes tags & installers)
chmod +x ship_update.sh
./ship_update.sh 1.1.0 "Added drag-and-drop link import and 4K VP9 fixes"
```

---

## 📜 License

Distributed under the **MIT License**. See `LICENSE` for more information.

---

## 🤝 Contributing & Acknowledgments

- Built on the media extraction engine [yt-dlp](https://github.com/yt-dlp/yt-dlp).
- Core conversion pipelines powered by [FFmpeg](https://ffmpeg.org).
- Webview desktop bridge enabled by [Eel](https://github.com/python-eel/Eel).

*Crafted by [Sachin Kant Jha](https://github.com/SachinKJha)*
