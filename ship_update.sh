#!/usr/bin/env bash
set -e

if [ -z "$1" ] || [ -z "$2" ]; then
  echo "Usage: ./ship_update.sh <version> \"<release notes>\""
  echo "Example: ./ship_update.sh 1.0.3 \"Added playlist support and fixed UI bugs\""
  exit 1
fi

NEW_VER="$1"
NOTES="$2"

echo "===================================================="
echo " 🚀 Preparing PulseTube Studio v${NEW_VER}"
echo "===================================================="

# 1. Automatically sync version across all 3 files
echo "[1/5] Syncing version v${NEW_VER} across main.py, installer.iss, and build_linux_deb.sh..."
sed -i "s/^APP_VERSION = .*/APP_VERSION = \"${NEW_VER}\"/" main.py
sed -i "s/^AppVersion=.*/AppVersion=${NEW_VER}/" installer.iss
sed -i "s/^OutputBaseFilename=.*/OutputBaseFilename=PulseTube_Setup_v${NEW_VER}/" installer.iss
sed -i "s/^APP_VER=.*/APP_VER=\"${NEW_VER}\"/" build_linux_deb.sh

# 2. Clean old builds
rm -rf build dist installer_out PulseTube.spec

# 3. Build Windows Installer (.exe)
echo "[2/5] Building Windows .exe Installer..."
wine python -m PyInstaller --noconsole --onedir --name "PulseTube" --icon "icon.ico" \
  --hidden-import bottle_websocket --collect-data eel --add-data "web;web" main.py --noconfirm
wine "C:\inno\ISCC.exe" installer.iss

# 4. Build Linux Installer (.deb)
echo "[3/5] Building Linux .deb Installer..."
./build_linux_deb.sh

# 5. Commit and Push source code to GitHub
echo "[4/5] Pushing source code to GitHub..."
git add .
git commit -m "Release v${NEW_VER}: ${NOTES}" || true
git push origin main

# 6. Create GitHub Release and upload both installers automatically
echo "[5/5] Publishing GitHub Release v${NEW_VER} & uploading installers..."
gh release create "v${NEW_VER}" \
  "installer_out/PulseTube_Setup_v${NEW_VER}.exe" \
  "installer_out/pulsetube_${NEW_VER}_amd64.deb" \
  --title "PulseTube Studio v${NEW_VER}" \
  --notes "${NOTES}"

echo "===================================================="
echo " ✅ v${NEW_VER} is LIVE on GitHub!"
echo "===================================================="