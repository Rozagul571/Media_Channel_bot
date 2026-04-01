# 📡 TENDERZON — Ishga tushirish qo'llanmasi

## Loyiha tuzilmasi

```
tenderzon/
├── app/
│   ├── core/
│   │   ├── config.py       ← .env dan sozlamalar
│   │   └── logger.py       ← Loglar (konsol + fayl)
│   ├── services/
│   │   ├── database.py     ← Dublikat oldini olish (SQLite)
│   │   ├── filter.py       ← Faqat xarid/qonun xabarlarini tanlaydi
│   │   ├── translator.py   ← Gemini AI: RU → UZ
│   │   ├── poster.py       ← Bot orqali kanalga yuboradi
│   │   └── monitor.py      ← Kanallarni kuzatadi (User session)
│   └── main.py             ← Ishga tushirish nuqtasi
├── .env                    ← SIZNING MA'LUMOTLARINGIZ
├── Dockerfile
├── docker-compose.yml
└── requirements.txt
```

---

## ⚡ 4 QADAMDA ISHGA TUSHIRISH

### QADAM 1 — Docker o'rnatish (server)
```bash
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER && newgrp docker
```

### QADAM 2 — .env faylini to'ldirish
```bash
nano .env
```

Faqat **4 ta qatorni** to'ldirish kerak:
```
TELEGRAM_API_ID=    ← https://my.telegram.org/apps dan oling
TELEGRAM_API_HASH=  ← https://my.telegram.org/apps dan oling
TELEGRAM_PHONE=     ← +998XXXXXXXXX (sizning raqamingiz)
TARGET_CHANNEL=     ← @sizning_kanalingiz
```

### QADAM 3 — BIRINCHI MARTA: OTP tasdiqlash
```bash
docker compose run --rm pipeline
```
Terminal sizdan **Telegram OTP kodini** so'raydi.
Telegram ilovangizni oching, kodni kiriting.
Bir marta bajariladi — sessiya saqlanadi.

### QADAM 4 — Fon rejimida ishga tushirish
```bash
docker compose up -d --build
```

---

## Asosiy buyruqlar

```bash
# Loglarni ko'rish
docker compose logs -f

# To'xtatish
docker compose down

# Qayta ishga tushirish
docker compose restart

# Konteyner ichiga kirish
docker compose exec pipeline bash
```

---

## Muammolar va yechimlar

| Muammo | Yechim |
|--------|--------|
| `SessionPasswordNeededError` | 2FA yoqilgan — parolingizni kiriting |
| `PeerIdInvalid` | Bot kanalingizda admin emas |
| `ChatWriteForbidden` | Botga "Xabar yuborish" ruxsati bering |
| Post chiqmayapti | `LOG_LEVEL=DEBUG` qo'yib qayta ishga tushiring |

---

## Namuna post ko'rinishi

```
📜 Davlat xaridlari yangiligi

⚖️ O'zbekiston Respublikasining davlat xaridlari
to'g'risidagi qonuniga yangi o'zgartirishlar kiritildi.
50 million so'mdan ortiq shartnomalar elektron
platformada joylashtirilishi shart.

🔗 Batafsil: https://lex.uz/docs/...

📌 @TenderzonUZ
```
