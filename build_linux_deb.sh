#!/usr/bin/env bash
set -e

echo "[1/4] Compiling Linux binary with PyInstaller..."
rm -f PulseTube.spec
pyinstaller --noconsole --onedir --name "PulseTube" --icon "icon.png" \
  --hidden-import bottle_websocket --collect-data eel \
  --add-data "web:web" main.py --noconfirm

PKG_DIR="deb_build/pulsetube_1.0.0_amd64"
echo "[2/4] Creating Debian package hierarchy..."
rm -rf deb_build
mkdir -p "$PKG_DIR/DEBIAN"
mkdir -p "$PKG_DIR/opt/pulsetube/web"
mkdir -p "$PKG_DIR/usr/bin"
mkdir -p "$PKG_DIR/usr/share/applications"
mkdir -p "$PKG_DIR/usr/share/icons/hicolor/256x256/apps"

# Copy compiled application and web assets to /opt/pulsetube
cp -r dist/PulseTube/* "$PKG_DIR/opt/pulsetube/"
cp -r web/* "$PKG_DIR/opt/pulsetube/web/"
cp icon.png "$PKG_DIR/usr/share/icons/hicolor/256x256/apps/pulsetube.png"

# Create launcher in /usr/bin
cat << 'EOF' > "$PKG_DIR/usr/bin/pulsetube"
#!/usr/bin/env bash
exec /opt/pulsetube/PulseTube "$@"
EOF
chmod 755 "$PKG_DIR/usr/bin/pulsetube"

# Create Desktop Menu & Shortcut Entry
cat << 'EOF' > "$PKG_DIR/usr/share/applications/pulsetube.desktop"
[Desktop Entry]
Name=PulseTube Studio
Comment=Batch YouTube MP3 & MP4 Downloader with Precision Trimming
Exec=/opt/pulsetube/PulseTube
Icon=pulsetube
Terminal=false
Type=Application
Categories=AudioVideo;Audio;Video;Network;
StartupNotify=true
EOF

# Create DEBIAN/control metadata
cat << 'EOF' > "$PKG_DIR/DEBIAN/control"
Package: pulsetube
Version: 1.0.0
Section: sound
Priority: optional
Architecture: amd64
Maintainer: Sachin Kant Jha <developer@pulsetube.local>
Description: PulseTube Studio - Batch MP3 and MP4 Downloader
 A YouTube-inspired frosted glass batch downloader supporting MP3/MP4,
 concurrent queues, timestamp trimming, and automatic GitHub updates.
EOF

echo "[3/4] Building .deb installer package..."
dpkg-deb --build "$PKG_DIR"
mkdir -p installer_out
mv deb_build/pulsetube_1.0.0_amd64.deb installer_out/

echo "[4/4] Done! Linux installer saved to: installer_out/pulsetube_1.0.0_amd64.deb"