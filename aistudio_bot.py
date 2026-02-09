#!/usr/bin/env python3
"""
Google AI Studio Video Isleme Bot

Kullanim:
    python aistudio_bot.py --video /path/to/video.mp4 --prompt "Bu videoyu analiz et"
    python aistudio_bot.py --video /path/to/video.mp4  # Varsayilan prompt kullanir

Cikti (stdout JSON):
    {"success": true, "response": "Videoda sunlar goruluyor..."}
    {"success": false, "error": "Session expired, please re-login"}
"""

import argparse
import asyncio
import json
import logging
import mimetypes
import sys
from pathlib import Path

import nodriver as uc
import nodriver.cdp.input_ as cdp_input

from config import (
    AISTUDIO_URL,
    DEFAULT_MODEL,
    RESPONSE_TIMEOUT,
    UPLOAD_TIMEOUT,
    POLL_INTERVAL,
    STABLE_COUNT,
)
from chrome_session import start_browser, ensure_session, save_cookies

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    stream=sys.stderr,  # Log'lar stderr'e, sonuc stdout'a
)
log = logging.getLogger(__name__)

DEFAULT_PROMPT = "Bu videoyu detayli olarak analiz et ve icerigini ozetle."


# ── Gercek AI Studio DOM Selectorleri ────────────────────────────────
# Prompt input:   textarea[aria-label="Enter a prompt"]
# Upload butonu:  button[aria-label="Insert images, videos, audio, or files"]
# Upload files:   menuitem "Upload files" (showOpenFilePicker kullanir, input[type=file] YOK)
# Run butonu:     button[type="submit"]  (aria-disabled="true" = bosta, "false" = aktif)
# Model yaniti:   .chat-turn-container.model [data-turn-role="Model"]
# Thumbs:         Yanit bitince thumbs up/down butonlari gorunur
# ─────────────────────────────────────────────────────────────────────


def output_result(success: bool, response: str = "", error: str = "") -> None:
    """Sonucu JSON olarak stdout'a yaz."""
    result = {"success": success}
    if success:
        result["response"] = response
    else:
        result["error"] = error
    print(json.dumps(result, ensure_ascii=False))


async def select_model(tab: uc.Tab, model_id: str = DEFAULT_MODEL) -> bool:
    """AI Studio'da model sec.

    DOM yapisi:
    - Run settings paneli: sag ust kosedeki tune ikonu ile acilir
    - Model selector: button.model-selector-card (ms-model-selector icinde)
    - Model listesi: .model-options-container button.content-button
    - Her butonun textContent'i model ID'sini icerir (ornegin "gemini-3-pro-preview")
    """
    log.info("Model seciliyor: %s", model_id)

    # 1. Run settings panelini ac (kapali olabilir)
    await tab.evaluate(
        """
        (() => {
            const card = document.querySelector('ms-model-selector button.model-selector-card');
            if (card) return;  // Panel zaten acik
            // Toggle butonu: aria-label="Toggle run settings panel"
            const toggleBtn = document.querySelector('button[aria-label="Toggle run settings panel"]')
                || document.querySelector('button.runsettings-toggle-button');
            if (toggleBtn) toggleBtn.click();
        })()
        """
    )
    await tab.sleep(1)

    # 2. Secili modeli kontrol et — zaten dogru mu?
    current = await tab.evaluate(
        """
        (() => {
            const card = document.querySelector('ms-model-selector button.model-selector-card');
            if (!card) return '';
            return card.textContent || '';
        })()
        """
    )
    current_text = str(current or "")
    log.info("Mevcut model: %s", current_text.replace("\\n", " ").strip()[:60])

    if model_id in current_text:
        log.info("Model zaten secili: %s", model_id)
        return True

    # 3. Model selector card'a tikla — model secim dialogu acilir
    await tab.evaluate(
        """
        (() => {
            const card = document.querySelector('ms-model-selector button.model-selector-card');
            if (card) card.click();
        })()
        """
    )
    await tab.sleep(1)

    # 4. Model listesinden istenen modeli bul ve tikla
    selected = await tab.evaluate(
        """
        ((targetId) => {
            const buttons = document.querySelectorAll('button.content-button');
            for (const btn of buttons) {
                const text = btn.textContent || '';
                if (text.includes(targetId)) {
                    btn.click();
                    return true;
                }
            }
            return false;
        })('""" + model_id + """')
        """
    )

    if not selected:
        log.error("Model bulunamadi: %s", model_id)
        return False

    await tab.sleep(0.5)
    log.info("Model secildi: %s", model_id)
    return True


async def upload_video(tab: uc.Tab, video_path: str) -> bool:
    """AI Studio'ya video yukle.

    AI Studio'da input[type=file] yok, showOpenFilePicker kullaniyor.
    Cozum: CDP Input.dispatchDragEvent ile dosya yolunu dogrudan Chrome'a veriyoruz.
    Chrome dosyayi diskten okur — base64 encode gereksiz, bellek sorunu yok.
    Headless modda da calisir.
    """
    log.info("Video yukleniyor: %s", video_path)

    video = Path(video_path)
    file_size = video.stat().st_size
    mime_type = mimetypes.guess_type(video_path)[0] or "video/mp4"
    file_name = video.name
    log.info("Dosya: %s (%.1f MB, %s)", file_name, file_size / 1024 / 1024, mime_type)

    # 1. Drop hedefinin koordinatlarini bul (prompt-box veya footer)
    coords = await tab.evaluate(
        """
        (() => {
            const target = document.querySelector('ms-prompt-box')
                || document.querySelector('footer')
                || document.querySelector('textarea');
            if (!target) return [0, 0];
            const rect = target.getBoundingClientRect();
            return [rect.x + rect.width / 2, rect.y + rect.height / 2];
        })()
        """
    )

    log.info("Drop hedefi ham sonuc: %s (type: %s)", coords, type(coords))

    if not coords or coords == [0, 0]:
        log.error("Drop hedefi bulunamadi!")
        return False

    # nodriver evaluate sonucu: [{'type':'number','value':X}, {'type':'number','value':Y}]
    def _extract_val(v):
        if isinstance(v, dict):
            return float(v.get("value", 0))
        return float(v)

    drop_x = _extract_val(coords[0])
    drop_y = _extract_val(coords[1])
    log.info("Drop hedefi koordinatlari: (%.0f, %.0f)", drop_x, drop_y)

    # 2. CDP DragData olustur — dosya yolunu dogrudan ver
    abs_path = str(video.absolute())
    drag_data = cdp_input.DragData(
        items=[
            cdp_input.DragDataItem(
                mime_type=mime_type,
                data="",
            )
        ],
        drag_operations_mask=1,  # Copy = 1
        files=[abs_path],
    )

    # 3. CDP drag event sirasi: dragEnter -> dragOver -> drop
    log.info("CDP drag event'leri gonderiliyor...")

    await tab.send(cdp_input.dispatch_drag_event(
        type_="dragEnter",
        x=drop_x,
        y=drop_y,
        data=drag_data,
    ))
    await tab.sleep(0.3)

    await tab.send(cdp_input.dispatch_drag_event(
        type_="dragOver",
        x=drop_x,
        y=drop_y,
        data=drag_data,
    ))
    await tab.sleep(0.3)

    await tab.send(cdp_input.dispatch_drag_event(
        type_="drop",
        x=drop_x,
        y=drop_y,
        data=drag_data,
    ))

    log.info("CDP drag event'leri gonderildi, dosya: %s", abs_path)
    await tab.sleep(1)

    # 4. Yuklemenin tamamlanmasini bekle
    return await _wait_for_upload_complete(tab)


async def _wait_for_upload_complete(tab: uc.Tab) -> bool:
    """Video yuklemesinin tamamlanmasini bekle."""
    log.info("Video yuklemesi bekleniyor (max %d sn)...", UPLOAD_TIMEOUT)

    elapsed = 0
    while elapsed < UPLOAD_TIMEOUT:
        await tab.sleep(2)
        elapsed += 2

        # Progress indicator kontrolu
        progress = await tab.query_selector('[role="progressbar"]')
        if progress:
            log.info("Yukleme devam ediyor... (%d sn)", elapsed)
            continue

        # "Uploading" / "Processing" metni kontrolu (JS ile daha guvenilir)
        still_uploading = await tab.evaluate(
            """
            (() => {
                const texts = ['Uploading', 'Processing', 'Loading'];
                const body = document.body.innerText;
                return texts.some(t => body.includes(t));
            })()
            """
        )
        if still_uploading:
            log.info("Yukleme/isleme devam ediyor... (%d sn)", elapsed)
            continue

        # Video thumbnail/preview var mi kontrol et
        has_media = await tab.evaluate(
            """
            (() => {
                // Yuklenmis medya elementi varsa yukleme tamamlanmis
                const media = document.querySelector(
                    'video, [class*="media-preview"], [class*="file-chip"], [class*="attachment"]'
                );
                return !!media;
            })()
            """
        )
        if has_media:
            log.info("Video yukleme tamamlandi — medya preview gorunuyor (%d sn)", elapsed)
            return True

        # 10 saniyeden sonra progress yoksa tamamlanmis say
        if elapsed >= 10:
            log.info("Progress yok, yukleme tamamlanmis kabul ediliyor (%d sn)", elapsed)
            return True

    log.warning("Video yukleme zaman asimi (%d sn)", UPLOAD_TIMEOUT)
    return True  # Yine de devam et


async def type_prompt(tab: uc.Tab, prompt: str) -> bool:
    """Prompt'u textarea'ya yaz."""
    log.info("Prompt yaziliyor: %s", prompt[:80] + "..." if len(prompt) > 80 else prompt)

    # AI Studio textarea selector'u (gercek DOM'dan)
    prompt_input = await tab.query_selector('textarea[aria-label="Enter a prompt"]')

    if not prompt_input:
        # Fallback: placeholder ile
        prompt_input = await tab.query_selector('textarea[placeholder*="Start typing"]')

    if not prompt_input:
        # Son fallback: herhangi bir textarea
        prompt_input = await tab.query_selector('textarea')

    if not prompt_input:
        log.error("Prompt textarea bulunamadi!")
        return False

    # Tikla, temizle, yaz
    await prompt_input.click()
    await tab.sleep(0.3)
    await prompt_input.clear_input()
    await tab.sleep(0.2)
    await prompt_input.send_keys(prompt)
    await tab.sleep(0.5)

    log.info("Prompt yazildi")
    return True


async def click_run(tab: uc.Tab) -> bool:
    """Run butonuna tikla."""
    log.info("Run butonuna tiklaniyor...")

    # Gercek selector: button[type="submit"] (class: ms-button-primary)
    run_btn = await tab.query_selector('button[type="submit"]')

    if not run_btn:
        log.warning("Submit butonu bulunamadi, Cmd+Enter deneniyor...")
        # Mac: Cmd+Enter, Linux: Ctrl+Enter
        await tab.send(cdp_input.dispatch_key_event(
            type_="keyDown",
            key="Enter",
            modifiers=4,  # Meta (Cmd) on Mac
        ))
        await tab.send(cdp_input.dispatch_key_event(
            type_="keyUp",
            key="Enter",
            modifiers=4,
        ))
        await tab.sleep(1)
        return True

    await run_btn.click()
    await tab.sleep(1)
    log.info("Run butonuna tiklandi")
    return True


async def wait_for_response(tab: uc.Tab) -> str:
    """Yanit tamamlanana kadar bekle ve metni don.

    AI Studio DOM yapisi:
    - Model yaniti: .chat-turn-container.model
    - Icerik:       [data-turn-role="Model"] (class: virtual-scroll-container model-prompt-container)
    - Metin:        ms-text-chunk icinde
    - Tamamlanma:   Thumbs up/down butonlari gorunur + metin degismeyi durdurur
    """
    log.info("Yanit bekleniyor (max %d sn)...", RESPONSE_TIMEOUT)

    # Yanitın baslamasini bekle
    await tab.sleep(3)

    previous_text = ""
    stable_count = 0
    elapsed = 0

    while elapsed < RESPONSE_TIMEOUT:
        await tab.sleep(POLL_INTERVAL)
        elapsed += POLL_INTERVAL

        # Model yanitini JavaScript ile al (en guvenilir yol)
        current_text = await tab.evaluate(
            """
            (() => {
                // Son model turn'unun icerigini al
                const modelTurns = document.querySelectorAll('.chat-turn-container.model');
                if (modelTurns.length === 0) return '';

                const lastTurn = modelTurns[modelTurns.length - 1];
                const contentDiv = lastTurn.querySelector('[data-turn-role="Model"]');
                if (contentDiv) {
                    return contentDiv.innerText || '';
                }

                // Fallback: ms-text-chunk
                const textChunk = lastTurn.querySelector('ms-text-chunk');
                if (textChunk) {
                    return textChunk.innerText || '';
                }

                return lastTurn.innerText || '';
            })()
            """
        )

        current_text = str(current_text or "").strip()

        # "edit", "more_vert", "Model" gibi UI metinlerini temizle
        for noise in ["edit\n", "more_vert\n", "edit\nmore_vert\n", "Model\n"]:
            if current_text.startswith(noise):
                current_text = current_text[len(noise):]

        # "Thinking" / "Expand to view" — model dusunme gostergesi, gercek yanit degil
        thinking_indicators = ["Thinking", "Expand to view", "chevron_right"]
        is_thinking = all(
            word in current_text for word in ["Thinking"]
        ) and len(current_text) < 200
        if is_thinking:
            log.info("Model dusunuyor... (%d sn)", elapsed)
            continue

        if not current_text:
            if elapsed > 15:
                log.warning("Hala yanit yok (%d sn)", elapsed)
            continue

        # Stabilite kontrolu
        if current_text == previous_text:
            stable_count += 1
            log.info(
                "Yanit stabil (%d/%d) — %d karakter, %d sn",
                stable_count, STABLE_COUNT, len(current_text), elapsed,
            )
            if stable_count >= STABLE_COUNT:
                # Ek dogrulama: thumbs butonlari gorunuyor mu?
                has_thumbs = await tab.evaluate(
                    """
                    (() => {
                        const modelTurns = document.querySelectorAll('.chat-turn-container.model');
                        if (modelTurns.length === 0) return false;
                        const last = modelTurns[modelTurns.length - 1];
                        const thumbs = last.querySelectorAll('[aria-label*="thumb"], [aria-label*="Good"], [aria-label*="Bad"]');
                        return thumbs.length >= 2;
                    })()
                    """
                )
                if has_thumbs:
                    log.info("Yanit tamamlandi (thumbs gorunuyor)! (%d karakter, %d sn)", len(current_text), elapsed)
                else:
                    log.info("Yanit tamamlandi (stabil)! (%d karakter, %d sn)", len(current_text), elapsed)
                return current_text
        else:
            stable_count = 0
            previous_text = current_text
            log.info("Yanit akiyor... (%d karakter, %d sn)", len(current_text), elapsed)

    # Timeout — mevcut metni don
    if previous_text:
        log.warning("Zaman asimi ama kismi yanit var (%d karakter)", len(previous_text))
        return previous_text

    return ""


async def process_video(video_path: str, prompt: str, headless: bool = False) -> None:
    """Ana islem: video yukle, prompt gonder, yanit al."""
    video = Path(video_path)
    if not video.exists():
        output_result(False, error=f"Video dosyasi bulunamadi: {video_path}")
        return

    supported = {".mp4", ".mpeg", ".mov", ".avi", ".flv", ".mpg", ".webm", ".wmv", ".3gpp", ".3gp"}
    if video.suffix.lower() not in supported:
        output_result(False, error=f"Desteklenmeyen video formati: {video.suffix}")
        return

    try:
        # 1. Chrome'a baglan
        browser = await start_browser(headless=headless)

        # 2. Oturumu kontrol et ve AI Studio'yu ac
        tab = await ensure_session(browser)

        # 3. Her islem icin yeni chat ac
        log.info("Yeni chat aciliyor...")
        tab = await browser.get(AISTUDIO_URL)
        await tab.sleep(3)

        # 4. Model sec
        if not await select_model(tab):
            log.warning("Model secilemedi, varsayilan ile devam ediliyor")

        # 5. Video yukle
        if not await upload_video(tab, str(video.absolute())):
            output_result(False, error="Video yuklenemedi")
            return

        # 6. Prompt yaz
        if not await type_prompt(tab, prompt):
            output_result(False, error="Prompt yazilamadi")
            return

        # 7. Run'a tikla
        if not await click_run(tab):
            output_result(False, error="Run butonuna tiklanamai")
            return

        # 8. Yanit bekle
        response_text = await wait_for_response(tab)

        if not response_text:
            output_result(False, error="Yanit alinamadi (zaman asimi)")
            return

        # 9. Cookie guncelle
        await save_cookies(browser)

        # 10. Sonucu don
        output_result(True, response=response_text)

    except RuntimeError as e:
        output_result(False, error=str(e))
    except Exception as e:
        log.exception("Beklenmeyen hata")
        output_result(False, error=f"Beklenmeyen hata: {e}")


def main():
    parser = argparse.ArgumentParser(
        description="Google AI Studio Video Isleme Bot",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ornekler:
  python aistudio_bot.py --video video.mp4 --prompt "Bu videoyu ozetle"
  python aistudio_bot.py --video video.mp4
  python aistudio_bot.py --video clip.mov --prompt "Videodaki kisileri say"
        """,
    )
    parser.add_argument(
        "--video", "-v",
        required=True,
        help="Video dosyasinin yolu",
    )
    parser.add_argument(
        "--prompt", "-p",
        default=DEFAULT_PROMPT,
        help=f"Gemini'ye gonderilecek prompt (varsayilan: '{DEFAULT_PROMPT}')",
    )
    parser.add_argument(
        "--headless",
        action="store_true",
        help="Chrome'u headless modda calistir (UI olmadan)",
    )

    args = parser.parse_args()

    uc.loop().run_until_complete(process_video(args.video, args.prompt, headless=args.headless))


if __name__ == "__main__":
    main()
