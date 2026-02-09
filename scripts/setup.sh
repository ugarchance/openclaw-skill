#!/bin/bash
# Gemini Video Skill — Tek seferlik kurulum
set -e

SKILL_DIR="$(cd "$(dirname "$0")/.." && pwd)"
echo "Skill dizini: $SKILL_DIR"

# 1. Sistem paketleri (noVNC dahil — login icin zorunlu)
echo "Sistem paketleri kontrol ediliyor..."
NEED_INSTALL=false
for pkg in xvfb x11vnc novnc; do
    if ! dpkg -s "$pkg" &>/dev/null; then
        NEED_INSTALL=true
        break
    fi
done

if [ "$NEED_INSTALL" = true ]; then
    echo "Eksik paketler kuruluyor (xvfb, x11vnc, novnc)..."
    apt-get update -qq
    apt-get install -y -qq xvfb x11vnc novnc >/dev/null
    echo "Sistem paketleri kuruldu."
else
    echo "Sistem paketleri zaten kurulu."
fi

# 2. Python venv olustur
if [ ! -d "$SKILL_DIR/venv" ]; then
    echo "Python venv olusturuluyor..."
    python3 -m venv "$SKILL_DIR/venv"
    echo "venv olusturuldu."
else
    echo "venv zaten mevcut."
fi

# 3. Bagimliliklari kur
echo "Python bagimliliklari kuruluyor..."
"$SKILL_DIR/venv/bin/pip" install -q -r "$SKILL_DIR/requirements.txt"
echo "Bagimliliklar kuruldu."

# 4. Kontrol
echo ""
echo "Kontrol:"
for bin in google-chrome xvfb-run x11vnc websockify python3; do
    if command -v "$bin" &>/dev/null; then
        echo "  [OK] $bin"
    else
        echo "  [EKSIK] $bin"
    fi
done

echo ""
echo "Kurulum tamamlandi!"
