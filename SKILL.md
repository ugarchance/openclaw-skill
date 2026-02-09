---
name: gemini-video
description: "Analyze videos and YouTube links using Google Gemini 3 Pro via AI Studio Playground. Receives a video file or YouTube URL, processes it through browser automation, sends a prompt, and returns Gemini's response. Works without an API key — uses the free Playground. Requires one-time Google login setup."
user-invocable: true
metadata: {"openclaw":{"emoji":"🎬","os":["linux"],"requires":{"bins":["python3","google-chrome","xvfb-run"]},"install":[{"id":"setup","kind":"custom","label":"Run setup script: {baseDir}/scripts/setup.sh"}]}}
---

# Gemini Video Analyzer

KRITIK KURALLAR — BUNLARI ASLA IHLAL ETME:

1. Kullaniciya ASLA teknik komut, script yolu, terminal talimati, SSH komutu, chrome://inspect adresi veya benzer teknik icerik gonderme. Kullanici Telegram'dan mesaj atiyor, terminal erisimi yok.
2. Login islemi icin SADECE asagidaki "Login Akisi" bolumunu takip et. Kendi yontemini UYDURMA. SSH tunnel, chrome://inspect, remote debugging gibi alternatif yontemler YASAK.
3. Login icin kullaniciya SADECE bir web linki (http://...) gonder. Bu linki asagidaki start_login.sh scripti uretir.
4. Tum bash komutlarini SEN calistir, kullaniciya gosterme.

## Adim 1 — Kurulum Kontrolu

Her video islemeden once:

```bash
test -d {baseDir}/venv && test -f {baseDir}/venv/bin/python && echo "VENV_OK" || echo "VENV_MISSING"
```

"VENV_MISSING" ise once kurulumu calistir:

```bash
bash {baseDir}/scripts/setup.sh
```

Kurulum basarisiz olursa kullaniciya de:
> Simdilik video analiz ozelligi kullanima hazir degil. En kisa surede aktif edilecek.

## Adim 2 — Oturum Kontrolu

```bash
test -f {baseDir}/cookies.dat && echo "SESSION_OK" || echo "SESSION_MISSING"
```

"SESSION_OK" ise → Adim 4'e (Video Isleme) git.
"SESSION_MISSING" ise → Adim 3'e (Login Akisi) git.

## Adim 3 — Login Akisi

SADECE bu adimlari takip et. Baska yontem KULLANMA.

### 3a. Login oturumu baslat

```bash
bash {baseDir}/scripts/start_login.sh
```

Bu komut stdout'a bir URL yazar (ornek: `http://193.111.77.248:6080/vnc.html`). Bu URL'yi al ve bir degiskende tut.

Eger komut hata verirse (noVNC eksik vs.), once setup calistir:
```bash
bash {baseDir}/scripts/setup.sh
```
Sonra start_login.sh'i tekrar dene.

### 3b. Kullaniciya SADECE su mesaji gonder

URL'yi komutun ciktisindaki gercek URL ile degistir:

> Video analiz icin tek seferlik bir giris yapman gerekiyor. 1 dakikani alacak!
>
> Su linki ac: [BURAYA_URL_GELECEK]
>
> Acilan sayfada "Connect" a bas, sonra Google hesabinla giris yap. Giris yaptiktan sonra ayni sayfada adres cubuguna aistudio.google.com yaz. Sayfa acilinca bana "tamam" yaz.

BASKA BIR SEY EKLEME. SSH, terminal, chrome://inspect gibi seylerden BAHSETME.

### 3c. Kullanicinin yanit vermesini bekle

Kullanici "tamam", "hazir", "yaptim", "oldu", "ok", "done" gibi onay verene kadar bekle.

### 3d. Oturumu kaydet

```bash
bash {baseDir}/scripts/save_session.sh
```

Cikti "OK:" ile basliyorsa → kullaniciya de:
> Giris basarili! Artik bana video gonderebilirsin.

Hata varsa → kullaniciya de:
> Giris tamamlanamadi. Tekrar deneyelim, sana yeni link gonderiyorum.
Sonra 3a'ya don.

### 3e. Bekleyen video varsa

Login sonrasi kullanicinin onceden gonderdigi bir video varsa, dogrudan Adim 4 ile devam et.

## Adim 4 — Video / YouTube Isleme

Kullanici iki tur icerik gonderebilir:
1. **Video dosyasi** (mp4, mov, webm vs.) → `--video` parametresi kullan
2. **YouTube linki** (youtube.com/watch?v=... veya youtu.be/...) → `--youtube` parametresi kullan

### 4a. Video dosyasi ile

```bash
xvfb-run --auto-servernum --server-args="-screen 0 1920x1080x24" {baseDir}/venv/bin/python {baseDir}/aistudio_bot.py --video "VIDEO_PATH" --prompt "PROMPT_TEXT" --model "MODEL_ID"
```

### 4b. YouTube linki ile

Kullanici mesajinda YouTube linki varsa (youtube.com veya youtu.be iceren URL):

```bash
xvfb-run --auto-servernum --server-args="-screen 0 1920x1080x24" {baseDir}/venv/bin/python {baseDir}/aistudio_bot.py --youtube "YOUTUBE_URL" --prompt "PROMPT_TEXT" --model "MODEL_ID"
```

### Parametreler

- `VIDEO_PATH`: Kullanicinin gonderdigi video dosyasinin yolu
- `YOUTUBE_URL`: Kullanicinin gonderdigi YouTube linki (ornek: `https://www.youtube.com/watch?v=abc123`)
- `PROMPT_TEXT`: Kullanicinin videoyla yazdigi mesaj. Belirtmemisse kullan: `Bu videoyu detayli olarak analiz et ve icerigini ozetle.`
- `MODEL_ID`: Kullanilacak model. Belirtmemisse `--model` parametresini ekleme (varsayilan: gemini-3-pro-preview)

ONEMLI: `--video` ve `--youtube` ayni anda KULLANILAMAZ. Birini sec.

### Model Secimi

| Kullanici ne derse | --model degeri |
|---|---|
| "pro", "pro kullan", "akilli model", "en iyi model" | gemini-3-pro-preview |
| "flash", "flash kullan", "hizli model", "hizli" | gemini-3-flash-preview |
| belirtmemisse | parametreyi ekleme (varsayilan pro kullanilir) |

Ornek: Kullanici "bunu flash ile analiz et" derse:
```bash
xvfb-run ... {baseDir}/aistudio_bot.py --video "..." --prompt "..." --model "gemini-3-flash-preview"
```

Ornek: Kullanici YouTube linki ile "bunu ozetle" derse:
```bash
xvfb-run ... {baseDir}/aistudio_bot.py --youtube "https://www.youtube.com/watch?v=abc123" --prompt "bunu ozetle"
```

## Adim 5 — Cikti Isleme

Komut stdout'a JSON yazar. Stdout'un **son satirini** parse et.

```json
{"success": true, "response": "..."}
{"success": false, "error": "..."}
```

**success: true** → `response` degerini oldugu gibi kullaniciya gonder.

**success: false** → Asagidaki tabloya gore sade Turkce mesaj gonder. ASLA teknik hata mesajini gosterme:

| error icindeki kelime | Kullaniciya mesaj |
|---|---|
| "oturumu bulunamadi" | cookies.dat sil (`rm -f {baseDir}/cookies.dat`) ve Adim 3'e don. Kullaniciya de: "Oturum suresi dolmus, tekrar giris yapmamiz gerekiyor." |
| "yuklenemedi" | "Video yuklenirken sorun olustu. Tekrar gonderir misin?" |
| "Desteklenmeyen" | "Bu format desteklenmiyor. mp4, mov veya webm olarak gonder." |
| "alinamadi" | "Sonuc alinamadi. Biraz sonra tekrar dener misin?" |
| "bulunamadi" | "Video okunamadi. Tekrar gonderir misin?" |
| (diger) | "Video islenirken sorun olustu. Biraz sonra tekrar dener misin?" |

## Desteklenen Icerik Turleri

**Video dosyalari:** mp4, mpeg, mov, avi, flv, mpg, webm, wmv, 3gpp, 3gp
**YouTube linkleri:** youtube.com/watch?v=..., youtu.be/..., youtube.com/shorts/...
