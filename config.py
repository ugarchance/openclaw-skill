import os
from pathlib import Path

BASE_DIR = Path(__file__).parent

AISTUDIO_URL = "https://aistudio.google.com/prompts/new_chat"
CHROME_DEBUG_HOST = "localhost"
CHROME_DEBUG_PORT = 9222
COOKIES_FILE = str(BASE_DIR / "cookies.dat")
CHROME_PROFILE_DIR = os.environ.get("CHROME_PROFILE_DIR", "/tmp/aistudio-chrome-profile")

DEFAULT_MODEL = "gemini-3-pro-preview"  # Kullanilacak model ID'si

RESPONSE_TIMEOUT = 180  # Video isleme icin max bekleme (sn)
UPLOAD_TIMEOUT = 60      # Video yukleme max bekleme (sn)
POLL_INTERVAL = 2        # Yanit kontrol araligi (sn)
STABLE_COUNT = 3         # Yanit degismeden kac kez kontrol edilmeli
