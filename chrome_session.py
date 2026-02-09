import asyncio
import logging
import nodriver as uc
from pathlib import Path
from config import (
    CHROME_DEBUG_HOST,
    CHROME_DEBUG_PORT,
    COOKIES_FILE,
    CHROME_PROFILE_DIR,
    AISTUDIO_URL,
)

log = logging.getLogger(__name__)


async def start_browser(connect_existing: bool = True, headless: bool = False) -> uc.Browser:
    """Chrome'a baglan. Once mevcut instance'a baglanmayi dene, yoksa yeni baslat."""
    if connect_existing:
        try:
            browser = await uc.start(
                host=CHROME_DEBUG_HOST,
                port=CHROME_DEBUG_PORT,
            )
            log.info("Mevcut Chrome instance'a baglandi (port %d)", CHROME_DEBUG_PORT)
            return browser
        except Exception as e:
            log.warning("Mevcut Chrome'a baglanamadi: %s — Yeni instance baslatiliyor", e)

    browser = await uc.start(
        headless=headless,
        user_data_dir=CHROME_PROFILE_DIR,
        browser_args=[
            f"--remote-debugging-port={CHROME_DEBUG_PORT}",
            "--no-first-run",
            "--no-default-browser-check",
        ],
    )
    log.info("Yeni Chrome instance baslatildi (headless=%s, profile: %s)", headless, CHROME_PROFILE_DIR)
    return browser


async def save_cookies(browser: uc.Browser) -> None:
    """Tarayici cerezlerini dosyaya kaydet."""
    try:
        await browser.cookies.save(COOKIES_FILE)
        log.info("Cookie'ler kaydedildi: %s", COOKIES_FILE)
    except Exception as e:
        log.error("Cookie kaydetme hatasi: %s", e)


async def load_cookies(browser: uc.Browser) -> bool:
    """Kayitli cerezleri tarayiciya yukle."""
    if not Path(COOKIES_FILE).exists():
        log.warning("Cookie dosyasi bulunamadi: %s", COOKIES_FILE)
        return False
    try:
        await browser.cookies.load(COOKIES_FILE)
        log.info("Cookie'ler yuklendi: %s", COOKIES_FILE)
        return True
    except Exception as e:
        log.error("Cookie yukleme hatasi: %s", e)
        return False


async def check_login(tab: uc.Tab) -> bool:
    """AI Studio sayfasinda Google login durumunu kontrol et.

    Login olunmussa sayfa normal yuklenir.
    Login olunmamissa Google sign-in sayfasina yonlendirir.
    """
    current_url = tab.url or ""

    # accounts.google.com'a yonlendirildiyse login degil
    if "accounts.google.com" in current_url:
        log.warning("Google login sayfasina yonlendirildi — oturum yok")
        return False

    # AI Studio sayfasindaysa ve "Sign in" butonu varsa login degil
    try:
        sign_in = await tab.query_selector('a[href*="accounts.google.com"]')
        if sign_in:
            log.warning("Sign-in butonu bulundu — oturum yok")
            return False
    except Exception:
        pass

    # "Start building" veya playground icerigi varsa login var
    try:
        playground = await tab.wait_for(text="Start building", timeout=5)
        if playground:
            log.info("AI Studio yuklendi — oturum aktif")
            return True
    except asyncio.TimeoutError:
        pass

    # Prompt input alani varsa login var
    try:
        prompt_input = await tab.query_selector('textarea, [contenteditable="true"]')
        if prompt_input:
            log.info("Prompt alani bulundu — oturum aktif")
            return True
    except Exception:
        pass

    log.warning("Login durumu belirlenemedi, URL: %s", current_url)
    return False


async def ensure_session(browser: uc.Browser) -> uc.Tab:
    """Oturumun aktif oldugunu garanti et. Yoksa cookie yukle ve tekrar dene.

    Returns:
        Aktif oturumlu AI Studio tab'i

    Raises:
        RuntimeError: Oturum kurulamazsa
    """
    tab = await browser.get(AISTUDIO_URL)
    await tab.sleep(3)  # Sayfanin yuklenmesini bekle

    if await check_login(tab):
        await save_cookies(browser)
        return tab

    # Cookie yukle ve tekrar dene
    log.info("Cookie'ler yukleniyor...")
    loaded = await load_cookies(browser)
    if loaded:
        tab = await browser.get(AISTUDIO_URL)
        await tab.sleep(3)
        if await check_login(tab):
            await save_cookies(browser)
            return tab

    raise RuntimeError(
        "Google oturumu bulunamadi! Lutfen Chrome'da AI Studio'ya manuel olarak login olun.\n"
        f"Chrome debug port: {CHROME_DEBUG_PORT}\n"
        f"URL: {AISTUDIO_URL}"
    )
