# AI Studio Video Bot

Google AI Studio Playground uzerinden Gemini ile video analizi yapan browser otomasyon botu.

Video + prompt gonderirsiniz, Gemini'nin yanitini JSON olarak alirsiniz. API key gerektirmez — Playground'u kullanir.

## Nasil Calisir

```
Video dosyasi --> [Bot] --> Chrome (AI Studio Playground) --> Gemini Pro --> JSON yanit
```

Bot browser otomasyonu ile:
1. AI Studio'da yeni chat acar
2. Istenen modeli secer (varsayilan: Gemini 3 Pro Preview)
3. Videoyu CDP drag-and-drop ile yukler
4. Prompt'u yazar ve Run'a tiklar
5. Yaniti bekler ve JSON olarak stdout'a yazar

## Gereksinimler

- Python 3.10+
- Google Chrome
- Google hesabi (AI Studio erisimi icin)
- **Sunucu icin:** Xvfb (sanal ekran)

## Kurulum

### 1. Projeyi indir

```bash
git clone <repo-url> ~/openclaw-skill
cd ~/openclaw-skill
```

### 2. Python ortamini kur

```bash
python3 -m venv venv
./venv/bin/pip install -r requirements.txt
```

### 3. Chrome kur (sunucu icin)

```bash
# Ubuntu/Debian
wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | sudo gpg --dearmor -o /usr/share/keyrings/google-chrome.gpg
echo 'deb [arch=amd64 signed-by=/usr/share/keyrings/google-chrome.gpg] http://dl.google.com/linux/chrome/deb/ stable main' | sudo tee /etc/apt/sources.list.d/google-chrome.list
sudo apt update && sudo apt install -y google-chrome-stable
```

### 4. Xvfb kur (sunucu icin — UI olmayan makinelerde gerekli)

```bash
sudo apt install -y xvfb
```

## Google Hesabina Login

Bot calismadan once bir kez Google hesabiniza login olmaniz gerekir. Cookie'ler kaydedilir ve sonraki calistirmalarda otomatik kullanilir.

### Mac/Desktop (ekranli makine)

```bash
./venv/bin/python login_and_save.py
```

Chrome acilir, Google'a login olun, terminale donup ENTER basin.

### Sunucu (ekransiz makine — SSH + Chrome DevTools yontemi)

**Adim 1:** Xvfb + Chrome'u baslatin:

```bash
# Xvfb baslat
Xvfb :99 -screen 0 1920x1080x24 +extension XTEST &

# Chrome'u baslat
export DISPLAY=:99
google-chrome \
  --no-sandbox \
  --no-first-run \
  --user-data-dir=/tmp/aistudio-chrome-profile \
  --remote-debugging-port=9222 \
  --remote-debugging-address=127.0.0.1 \
  "https://accounts.google.com" &
```

**Adim 2:** Kendi bilgisayarinizdan SSH tunnel acin:

```bash
ssh -L 9222:localhost:9222 kullanici@sunucu-ip
```

**Adim 3:** Kendi bilgisayarinizdaki Chrome'da su adresi acin:

```
chrome://inspect/#devices
```

"Discover network targets" > "Configure" > `localhost:9222` ekleyin.
Sunucudaki sayfa gorunecek — "inspect" tiklayin ve Google'a login olun.

**Adim 4:** Cookie'leri kaydedin:

```bash
cd ~/openclaw-skill
DISPLAY=:99 ./venv/bin/python3 -c "
import nodriver as uc
async def save():
    browser = await uc.start(host='localhost', port=9222)
    await browser.cookies.save('cookies.dat')
    all_c = await browser.cookies.get_all()
    print(f'Saved {len(all_c)} cookies')
uc.loop().run_until_complete(save())
"
```

**Adim 5:** Chrome ve Xvfb'yi kapatabilirsiniz:

```bash
killall google-chrome Xvfb
```

## Kullanim

### Mac/Desktop

```bash
./venv/bin/python aistudio_bot.py --video video.mp4 --prompt "Bu videoyu analiz et"
```

### Sunucu (Xvfb ile)

```bash
xvfb-run --auto-servernum --server-args="-screen 0 1920x1080x24" \
  ./venv/bin/python aistudio_bot.py --video video.mp4 --prompt "Bu videoyu analiz et"
```

### Cikti

Stdout'a JSON yazilir:

```json
{"success": true, "response": "Videoda renkli test desenleri ve dijital sayac goruluyor..."}
```

Hata durumunda:

```json
{"success": false, "error": "Video yuklenemedi"}
```

Log'lar stderr'e yazilir, programatik kullanimda sadece stdout'u parse edin.

### Parametreler

| Parametre | Zorunlu | Aciklama |
|-----------|---------|----------|
| `--video`, `-v` | Evet | Video dosyasinin yolu |
| `--prompt`, `-p` | Hayir | Gemini'ye gonderilecek prompt (varsayilan: genel analiz) |
| `--headless` | Hayir | Chrome'u headless modda calistir (onerilen degil, Xvfb kullanin) |

### Desteklenen Video Formatlari

mp4, mpeg, mov, avi, flv, mpg, webm, wmv, 3gpp, 3gp

## Yapilandirma

`config.py` dosyasini duzenleyin:

```python
DEFAULT_MODEL = "gemini-3-pro-preview"  # Kullanilacak model
RESPONSE_TIMEOUT = 180                   # Yanit bekleme suresi (sn)
UPLOAD_TIMEOUT = 60                      # Video yukleme suresi (sn)
CHROME_PROFILE_DIR = "/tmp/aistudio-chrome-profile"  # Chrome profil dizini
```

Model ID'leri AI Studio'dan alinabilir. Ornekler:
- `gemini-3-pro-preview` — En akilli, yavas
- `gemini-3-flash-preview` — Hizli, ucretli API'de ucuz

## Dosya Yapisi

```
openclaw-skill/
├── aistudio_bot.py      # Ana bot scripti (CLI)
├── chrome_session.py    # Chrome oturum yonetimi
├── config.py            # Ayarlar
├── login_and_save.py    # Tek seferlik Google login helper
├── requirements.txt     # Python bagimliliklari (nodriver)
├── cookies.dat          # Kaydedilmis oturum cerezleri (gitignore)
└── README.md
```

## Onemli Notlar

- **Headless mod onerilmez.** AI Studio headless Chrome'u algilar ve hata verir. Sunucuda `xvfb-run` kullanin.
- **Cookie suresi.** Google oturumu birkaç hafta gecerli kalir. Hata alirsan tekrar login ol.
- **Rate limit.** AI Studio Playground'da rate limit vardir. Cok sik istek gondermekten kacinin.
- **Model degisebilir.** Google model adlarini/ID'lerini degistirebilir. Hata alirsan `config.py`'deki `DEFAULT_MODEL`'i guncelle.

## Sorun Giderme

| Sorun | Cozum |
|-------|-------|
| "Google oturumu bulunamadi" | Login islemini tekrarlayin |
| "An internal error has occurred" | Headless kullanmayin, `xvfb-run` ile calistirin |
| "Video yuklenemedi" | Desteklenen formatlari kontrol edin |
| "Model bulunamadi" | `config.py`'de model ID'sini guncelleyin |
| "Drop hedefi bulunamadi" | AI Studio DOM degismis olabilir, selectorleri guncelleyin |
| Yanit cok kisa/bos | `RESPONSE_TIMEOUT` degeri artirin |
