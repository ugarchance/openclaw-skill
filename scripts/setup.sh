#!/bin/bash
# Gemini Video Skill — Tek seferlik kurulum
set -e

SKILL_DIR="$(cd "$(dirname "$0")/.." && pwd)"
echo "Skill dizini: $SKILL_DIR"

# 1. Python venv olustur
if [ ! -d "$SKILL_DIR/venv" ]; then
    echo "Python venv olusturuluyor..."
    python3 -m venv "$SKILL_DIR/venv"
    echo "venv olusturuldu."
else
    echo "venv zaten mevcut."
fi

# 2. Bagimliliklari kur
echo "Bagimliliklar kuruluyor..."
"$SKILL_DIR/venv/bin/pip" install -q -r "$SKILL_DIR/requirements.txt"
echo "Bagimliliklar kuruldu."

# 3. Gerekli programlari kontrol et
echo ""
echo "Gereksinimler kontrol ediliyor..."

check_bin() {
    if command -v "$1" &>/dev/null; then
        echo "  [OK] $1"
    else
        echo "  [EKSIK] $1 — kurulum gerekli"
    fi
}

check_bin google-chrome
check_bin xvfb-run
check_bin python3
check_bin x11vnc
check_bin websockify

# 4. noVNC kontrolu (opsiyonel — mobilden login icin)
echo ""
if command -v websockify &>/dev/null && [ -d /usr/share/novnc ]; then
    echo "noVNC: [OK] — mobilden login yapilabilir"
else
    echo "noVNC: [EKSIK] — mobilden login icin kur:"
    echo "  sudo apt install -y novnc x11vnc"
    echo "  (opsiyonel, SSH tunnel yontemi noVNC olmadan da calisir)"
fi

echo ""
echo "Kurulum tamamlandi!"
echo ""
echo "Simdi Google login yap:"
echo "  bash $SKILL_DIR/scripts/login.sh"
echo ""
echo "Login yontemleri:"
echo "  1. noVNC ile (mobilden de olur) — noVNC kuruluysa otomatik acar"
echo "  2. SSH tunnel + Chrome DevTools — noVNC yoksa bu kullanilir"
