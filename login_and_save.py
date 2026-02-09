#!/usr/bin/env python3
"""
Chrome'u ac, Google'a login ol, cookie'leri kaydet.

1. Chrome acilir
2. Sen Google'a login ol
3. AI Studio'ya git
4. Terminal'e donup Enter'a bas
5. Cookie'ler kaydedilir
"""
import asyncio
import nodriver as uc
from config import AISTUDIO_URL, COOKIES_FILE, CHROME_PROFILE_DIR


async def main():
    print(f"Chrome baslatiliyor (profil: {CHROME_PROFILE_DIR})...")
    browser = await uc.start(
        headless=False,
        user_data_dir=CHROME_PROFILE_DIR,
    )

    print(f"AI Studio aciliyor: {AISTUDIO_URL}")
    tab = await browser.get(AISTUDIO_URL)

    print("\n" + "=" * 60)
    print("SIMDI:")
    print("1. Chrome'da Google hesabina login ol")
    print("2. AI Studio'nun yuklendigini gor")
    print("3. Buraya donup ENTER'a bas")
    print("=" * 60)

    input("\n>>> Login olduktan sonra ENTER'a bas... ")

    print("Cookie'ler kaydediliyor...")
    await browser.cookies.save(COOKIES_FILE)
    print(f"Cookie'ler kaydedildi: {COOKIES_FILE}")

    # Dogrulama
    all_cookies = await browser.cookies.get_all()
    google_cookies = [c for c in all_cookies if "google" in getattr(c, "domain", "")]
    print(f"Toplam {len(all_cookies)} cookie, {len(google_cookies)} tanesi Google'a ait")

    print("\nTamam! Simdi bu cookie dosyasini sunucuya atabilirsin.")
    print("Chrome kapatiliyor...")


if __name__ == "__main__":
    uc.loop().run_until_complete(main())
