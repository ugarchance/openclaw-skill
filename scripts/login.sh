#!/bin/bash
# Gemini Video Skill — Google Login
# Iki yontem: noVNC (mobilden de olur) veya SSH tunnel (masaustu gerektirir)
set -e

SKILL_DIR="$(cd "$(dirname "$0")/.." && pwd)"
PROFILE_DIR="${CHROME_PROFILE_DIR:-/tmp/aistudio-chrome-profile}"
NOVNC_PORT=6080
VNC_PORT=5900

echo "=== Google AI Studio Login ==="
echo ""

# --- Mac/Desktop ---
if [[ "$(uname)" == "Darwin" ]]; then
    echo "Mac tespit edildi. Chrome acilacak, Google'a login olun."
    "$SKILL_DIR/venv/bin/python" "$SKILL_DIR/login_and_save.py"
    exit 0
fi

# --- Linux Sunucu ---
cleanup() {
    echo ""
    echo "Temizleniyor..."
    killall -9 novnc_proxy x11vnc Xvfb google-chrome 2>/dev/null || true
    echo "Temizlendi."
}
trap cleanup EXIT

# Mevcut islemleri temizle
killall -9 novnc_proxy x11vnc Xvfb google-chrome 2>/dev/null || true
sleep 1

# noVNC kurulu mu kontrol et
HAS_NOVNC=false
if command -v novnc_proxy &>/dev/null; then
    HAS_NOVNC=true
elif [ -f /usr/share/novnc/utils/novnc_proxy ]; then
    HAS_NOVNC=true
    NOVNC_CMD="/usr/share/novnc/utils/novnc_proxy"
elif command -v websockify &>/dev/null && [ -d /usr/share/novnc ]; then
    HAS_NOVNC=true
fi

# noVNC yoksa kurmayı oner
if [ "$HAS_NOVNC" = false ]; then
    echo "noVNC kurulu degil. Mobilden login icin noVNC gerekli."
    echo ""
    echo "Kurmak icin:"
    echo "  sudo apt install -y novnc x11vnc"
    echo ""
    echo "noVNC olmadan SSH tunnel yontemi kullanilacak."
    echo ""
fi

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

echo "Chrome baslatildi."
echo ""

# noVNC varsa web tabanli erisim ac
if [ "$HAS_NOVNC" = true ]; then
    # x11vnc baslat
    x11vnc -display :99 -nopw -forever -shared -rfbport $VNC_PORT -noxrecord -noxfixes -noxdamage &
    sleep 1

    # noVNC proxy baslat
    if command -v novnc_proxy &>/dev/null; then
        novnc_proxy --vnc localhost:$VNC_PORT --listen $NOVNC_PORT &
    elif [ -n "$NOVNC_CMD" ]; then
        "$NOVNC_CMD" --vnc localhost:$VNC_PORT --listen $NOVNC_PORT &
    else
        websockify --web /usr/share/novnc $NOVNC_PORT localhost:$VNC_PORT &
    fi
    sleep 2

    SERVER_IP=$(hostname -I 2>/dev/null | awk '{print $1}' || echo "<sunucu-ip>")

    echo "============================================"
    echo "  TARAYICIDAN LOGIN (mobil veya masaustu)"
    echo "============================================"
    echo ""
    echo "  Telefonunuzdan veya bilgisayarinizdan acin:"
    echo ""
    echo "    http://$SERVER_IP:$NOVNC_PORT/vnc.html"
    echo ""
    echo "  Connect'e basin, Google'a login olun."
    echo "============================================"
else
    echo "============================================"
    echo "  SSH TUNNEL ILE LOGIN (masaustu gerekli)"
    echo "============================================"
    echo ""
    echo "  1. SSH tunnel acin:"
    echo "     ssh -L 9222:localhost:9222 <kullanici>@<sunucu-ip>"
    echo ""
    echo "  2. Chrome'da acin: chrome://inspect/#devices"
    echo "  3. Configure > localhost:9222 ekleyin"
    echo "  4. 'inspect' tiklayin ve Google'a login olun"
    echo "============================================"
fi

echo ""
read -p "Login tamamlaninca ENTER basin >>> "

# Cookie kaydet
echo "Cookie'ler kaydediliyor..."
cd "$SKILL_DIR"
DISPLAY=:99 "$SKILL_DIR/venv/bin/python3" -c "
import nodriver as uc
async def save():
    browser = await uc.start(host='localhost', port=9222)
    await browser.cookies.save('cookies.dat')
    all_c = await browser.cookies.get_all()
    print(f'Saved {len(all_c)} cookies')
uc.loop().run_until_complete(save())
"

echo ""
echo "Cookie'ler kaydedildi! Skill kullanima hazir."
