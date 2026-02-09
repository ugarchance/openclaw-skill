#!/bin/bash
# Gemini Video Skill — Cookie kaydet ve login oturumunu kapat
set -e

SKILL_DIR="$(cd "$(dirname "$0")/.." && pwd)"

# Cookie kaydet
cd "$SKILL_DIR"
DISPLAY=:99 "$SKILL_DIR/venv/bin/python3" -c "
import nodriver as uc
async def save():
    browser = await uc.start(host='localhost', port=9222)
    await browser.cookies.save('cookies.dat')
    all_c = await browser.cookies.get_all()
    print(f'OK:{len(all_c)}')
uc.loop().run_until_complete(save())
" 2>/dev/null

# Temizle — Chrome'u graceful kapat
killall google-chrome 2>/dev/null || true
sleep 3
killall -9 google-chrome 2>/dev/null || true
killall -9 novnc_proxy x11vnc Xvfb 2>/dev/null || true

# UFW varsa 6080 portunu kapat
if command -v ufw &>/dev/null; then
    ufw deny 6080/tcp >/dev/null 2>&1 || true
fi
