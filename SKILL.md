---
name: gemini-video
description: "Analyze videos using Google Gemini 3 Pro via AI Studio Playground. Receives a video file, uploads it to AI Studio through browser automation, sends a prompt, and returns Gemini's response. Works without an API key — uses the free Playground. Requires one-time Google login setup."
user-invocable: true
metadata: {"openclaw":{"emoji":"🎬","os":["linux"],"requires":{"bins":["python3","google-chrome","xvfb-run"]},"install":[{"id":"setup","kind":"custom","label":"Run setup script: {baseDir}/scripts/setup.sh"}]}}
---

# Gemini Video Analyzer

Video dosyalarini Google AI Studio Playground uzerinden Gemini 3 Pro Preview ile analiz eder. API key gerektirmez.

ONEMLI: Bu skill'deki tum komutlari SEN (agent) calistir. Kullaniciya ASLA teknik komut, script yolu veya terminal talimati gonderme. Kullanici Telegram'dan mesaj atiyor, terminal erisimi yok. Kullaniciya sadece sade, anlasilir Turkce mesaj gonder.

## Calistirmadan Once — Kurulum Kontrolu

Video isleme komutunu calistirmadan once su kontrolleri yap:

### 1. venv var mi?

```bash
test -d {baseDir}/venv && echo "OK" || echo "MISSING"
```

"MISSING" ise kullaniciya mesaj gonder ve DURDUR:

> Simdilik video analiz ozelligi kullanima hazir degil. En kisa surede aktif edilecek.

### 2. Google oturumu aktif mi?

```bash
test -f {baseDir}/cookies.dat && echo "OK" || echo "MISSING"
```

"MISSING" ise → Login Akisi'na git (asagida).

Her iki kontrol de "OK" ise → Video Isleme'ye git.

## Login Akisi (oturum yoksa)

Kullanici login yapmamissa asagidaki adimlari izle:

### Adim 1 — Login oturumu baslat

```bash
bash {baseDir}/scripts/start_login.sh
```

Bu komut bir URL dondurur (ornegin `http://193.111.77.248:6080/vnc.html`). Bu URL'yi al.

### Adim 2 — Kullaniciya link gonder

Kullaniciya su mesaji gonder (URL'yi komutun ciktisindaki gercek URL ile degistir):

> Video analiz ozelligini kullanabilmek icin tek seferlik bir giris yapman gerekiyor. Cok kisa surecek!
>
> 1. Su linki telefonundan veya bilgisayarindan ac: BURAYA_URL_GELECEK
> 2. Acilan sayfada "Connect" butonuna bas
> 3. Google hesabinla giris yap
> 4. Giris yaptiktan sonra adres cubuguna aistudio.google.com yaz ve sayfanin acildigini gordukten sonra bana "tamam" yaz

### Adim 3 — Kullanicinin "tamam" demesini bekle

Kullanici "tamam", "hazir", "yaptim", "oldu" gibi bir onay mesaji gonderene kadar bekle.

### Adim 4 — Oturumu kaydet

```bash
bash {baseDir}/scripts/save_session.sh
```

Cikti "OK:" ile basliyorsa basarili. Kullaniciya mesaj gonder:

> Giris basarili! Artik video gonderebilirsin, ben analiz edeyim.

Cikti "OK:" ile baslamiyorsa veya hata varsa:

> Giris sirasinda bir sorun olustu. Lutfen tekrar deneyelim — sana yeni bir link gonderiyorum.

Ve Adim 1'e don.

### Adim 5 — Eger kullanici video da gondermisse

Login tamamlandiktan sonra, eger kullanicinin bekleyen bir videosu varsa dogrudan Video Isleme adimiyla devam et.

## Video Isleme

Asagidaki komutu SEN calistir:

```bash
xvfb-run --auto-servernum --server-args="-screen 0 1920x1080x24" {baseDir}/venv/bin/python {baseDir}/aistudio_bot.py --video "VIDEO_PATH" --prompt "PROMPT_TEXT"
```

- `VIDEO_PATH`: Kullanicinin gonderdigi video dosyasinin yolu
- `PROMPT_TEXT`: Kullanicinin videoyla birlikte yazdigi mesaj

Eger kullanici prompt belirtmemisse (sadece video gondermisse):
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

**`success: true` ise:** `response` degerini dogrudan kullaniciya gonder. Basina/sonuna ekstra bir sey ekleme.

**`success: false` ise:** Kullaniciya teknik detay gosterme. Sade mesaj gonder:

| error icerigi | Kullaniciya mesaj |
|---|---|
| "Google oturumu bulunamadi" | "Oturum suresi dolmus. Tekrar giris yapmamiz gerekiyor, sana link gonderiyorum." Sonra Login Akisi'na don. |
| "Video yuklenemedi" | "Video yuklenirken bir sorun olustu. Lutfen tekrar gonderir misin?" |
| "Desteklenmeyen video formati" | "Bu video formati desteklenmiyor. Lutfen mp4, mov veya webm olarak gonder." |
| "Yanit alinamadi" | "Video islendi ama sonuc alinamadi. Biraz sonra tekrar dener misin?" |
| "Video dosyasi bulunamadi" | "Video dosyasi okunamadi. Lutfen tekrar gonder." |
| Diger | "Video islenirken bir sorun olustu. Biraz sonra tekrar dener misin?" |

ONEMLI: "Google oturumu bulunamadi" hatasinda cookies.dat dosyasini sil ve Login Akisi'ni baslat:

```bash
rm -f {baseDir}/cookies.dat
```

## Desteklenen Video Formatlari

mp4, mpeg, mov, avi, flv, mpg, webm, wmv, 3gpp, 3gp

## Kurulum Rehberi (sunucu yoneticisi icin — kullaniciya gosterme)

Bu bolum sadece sunucu yoneticisinin ilk kurulumu icindir.

### 1. Gerekli paketler

```bash
sudo apt install -y python3 python3-venv google-chrome-stable xvfb x11vnc novnc
```

### 2. Skill kurulumu

```bash
bash {baseDir}/scripts/setup.sh
```

### 3. Google login

Login'i kullanicilar kendileri noVNC uzerinden yapar. Yonetici login yapmak isterse:

```bash
bash {baseDir}/scripts/login.sh
```
