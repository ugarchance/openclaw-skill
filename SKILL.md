---
name: gemini-video
description: "Analyze videos using Google Gemini 3 Pro via AI Studio Playground. Receives a video file, uploads it to AI Studio through browser automation, sends a prompt, and returns Gemini's response. Works without an API key — uses the free Playground. Requires one-time Google login setup."
user-invocable: true
metadata: {"openclaw":{"emoji":"🎬","os":["linux"],"requires":{"bins":["python3","google-chrome","xvfb-run"]},"install":[{"id":"setup","kind":"custom","label":"Run setup script: {baseDir}/scripts/setup.sh"}]}}
---

# Gemini Video Analyzer

Video dosyalarini Google AI Studio Playground uzerinden Gemini 3 Pro Preview ile analiz eder. API key gerektirmez.

## Calistirmadan Once — Kurulum Kontrolu

Video isleme komutunu calistirmadan once su kontrolleri yap:

### 1. venv var mi?

```bash
test -d {baseDir}/venv && echo "OK" || echo "MISSING"
```

Eger "MISSING" donerse kullaniciya su mesaji gonder:

> Gemini Video skill'i henuz kurulmamis. Sunucu yoneticisinin kurulum yapmasi gerekiyor:
> `bash {baseDir}/scripts/setup.sh`

Ve islem DURDUR, komutu calistirma.

### 2. Google oturumu var mi?

```bash
test -f {baseDir}/cookies.dat && echo "OK" || echo "MISSING"
```

Eger "MISSING" donerse kullaniciya su mesaji gonder:

> Google oturumu bulunamadi. Tek seferlik login gerekiyor.
> Sunucu yoneticisi su komutu calistirmali: `bash {baseDir}/scripts/login.sh`
> Login telefondan veya bilgisayardan yapilabilir (noVNC ile).

Ve islem DURDUR, komutu calistirma.

## Kullanim

Kontroller basarili ise asagidaki komutu calistir:

```bash
xvfb-run --auto-servernum --server-args="-screen 0 1920x1080x24" {baseDir}/venv/bin/python {baseDir}/aistudio_bot.py --video "VIDEO_PATH" --prompt "PROMPT_TEXT"
```

- `VIDEO_PATH`: Analiz edilecek video dosyasinin yolu
- `PROMPT_TEXT`: Kullanicinin videoyla birlikte gonderdigi mesaj

Eger kullanici prompt belirtmemisse (sadece video gondermisse) varsayilan prompt kullan:
```
Bu videoyu detayli olarak analiz et ve icerigini ozetle.
```

## Cikti Isleme

Komut stdout'a JSON yazar. Sadece stdout'un **son satirini** parse et (onceki satirlar log olabilir).

Basarili:
```json
{"success": true, "response": "Videoda sunlar goruluyor..."}
```

Basarisiz:
```json
{"success": false, "error": "Hata aciklamasi"}
```

**`success: true` ise:** `response` degerini dogrudan kullaniciya gonder.

**`success: false` ise:** Hata turune gore kullaniciya bilgi ver:

| error icerigi | Kullaniciya mesaj |
|---|---|
| "Google oturumu bulunamadi" | "Google oturumum suresi dolmus, yonetici tekrar login yapmali." |
| "Video yuklenemedi" | "Video yuklenemedi. Desteklenen formatlar: mp4, mov, avi, webm, mkv" |
| "Desteklenmeyen video formati" | "Bu video formati desteklenmiyor. Lutfen mp4, mov veya webm gonderin." |
| "Yanit alinamadi" | "Gemini yanit veremedi, lutfen biraz sonra tekrar deneyin." |
| Diger | "Video islenirken bir hata olustu: [hata mesaji]" |

## Desteklenen Video Formatlari

mp4, mpeg, mov, avi, flv, mpg, webm, wmv, 3gpp, 3gp

## Kurulum (tek seferlik — sunucu yoneticisi yapar)

### 1. Bagimliliklari kur

```bash
bash {baseDir}/scripts/setup.sh
```

### 2. Google'a login ol

noVNC kuruluysa telefondan login yapilabilir:

```bash
bash {baseDir}/scripts/login.sh
```

Script, noVNC varsa web tabanli erisim acar (mobilden de calisan).
noVNC yoksa SSH tunnel yontemini kullanir (masaustu gerektirir).

noVNC kurmak icin: `sudo apt install -y novnc x11vnc`

### 3. Login yenileme

Google oturumu birkac hafta gecerli kalir. Suresi dolunca bot "Google oturumu bulunamadi" hatasi verir. Tekrar login icin ayni komutu calistir:

```bash
bash {baseDir}/scripts/login.sh
```

## Sorun Giderme

| Hata | Cozum |
|------|-------|
| "Google oturumu bulunamadi" | `bash {baseDir}/scripts/login.sh` ile tekrar login ol |
| "An internal error has occurred" | xvfb-run kullanildigini dogrula, --headless kullanma |
| "Video yuklenemedi" | Desteklenen video formatini kontrol et |
| Yanit bos geliyor | AI Studio rate limit olabilir, biraz bekle ve tekrar dene |
| "Drop hedefi bulunamadi" | AI Studio DOM degismis olabilir, skill guncellenmeli |
