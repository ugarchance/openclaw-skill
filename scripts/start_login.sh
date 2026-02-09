#!/bin/bash
# Gemini Video Skill — Login oturumu baslat (noVNC)
# Cikti: noVNC URL'sini stdout'a yazar
set -e

SKILL_DIR="$(cd "$(dirname "$0")/.." && pwd)"
PROFILE_DIR="${CHROME_PROFILE_DIR:-/tmp/aistudio-chrome-profile}"
NOVNC_PORT=6080
VNC_PORT=5900

# Onceki islemleri temizle
killall google-chrome 2>/dev/null || true
sleep 1
killall -9 google-chrome novnc_proxy x11vnc Xvfb 2>/dev/null || true
sleep 1

# Xvfb baslat
Xvfb :99 -screen 0 1920x1080x24 +extension XTEST &
sleep 1

# Chrome baslat
export DISPLAY=:99
google-chrome \
    --no-sandbox \
    --no-first-run \
    --user-data-dir="$PROFILE_DIR" \
    --remote-debugging-port=9222 \
    --remote-debugging-address=127.0.0.1 \
    "https://accounts.google.com" &
sleep 3

# x11vnc baslat
x11vnc -display :99 -nopw -forever -shared -rfbport $VNC_PORT -noxrecord -noxfixes -noxdamage &>/dev/null &
sleep 1

# noVNC proxy baslat
if command -v novnc_proxy &>/dev/null; then
    novnc_proxy --vnc localhost:$VNC_PORT --listen $NOVNC_PORT &>/dev/null &
elif [ -f /usr/share/novnc/utils/novnc_proxy ]; then
    /usr/share/novnc/utils/novnc_proxy --vnc localhost:$VNC_PORT --listen $NOVNC_PORT &>/dev/null &
elif command -v websockify &>/dev/null; then
    websockify --web /usr/share/novnc $NOVNC_PORT localhost:$VNC_PORT &>/dev/null &
else
    echo "ERROR:noVNC kurulu degil"
    exit 1
fi
sleep 2

# Sunucu IP'sini bul ve URL'yi stdout'a yaz
SERVER_IP=$(hostname -I 2>/dev/null | awk '{print $1}' || echo "sunucu-ip")
echo "http://$SERVER_IP:$NOVNC_PORT/vnc.html"
