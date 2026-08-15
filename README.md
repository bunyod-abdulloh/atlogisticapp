# A&T Logistics — Django backend

Cargo tracking API + chiroyli admin panel (Jazzmin).

## 1. O'rnatish

```bash
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env            # va SECRET_KEY'ni o'zgartiring
python manage.py migrate
python manage.py createsuperuser
```

## 2. Demo ma'lumot bilan sinash

Frontend'dagi (`tracking-frontend/script.js`) `DEMO_DATA` bilan bir xil 3 ta yukni
bazaga yozadi — shu bilan `DEMO_MODE = false` qilib real backend'ni sinashingiz mumkin.

```bash
python manage.py seed_demo_data
```

## 3. Ishga tushirish

```bash
python manage.py runserver
```

- API: `GET http://127.0.0.1:8000/api/track/ATL-24081/`
- Admin: `http://127.0.0.1:8000/admin/`

## 4. Frontend bilan ulash

`tracking-frontend/script.js` faylida:

```js
const DEMO_MODE = false;               // demo o'chiriladi
const API_BASE = "http://127.0.0.1:8000/api";
```

Agar frontend boshqa portda ochilsa (masalan VSCode Live Server — `127.0.0.1:5500`),
`.env` faylidagi `CORS_ALLOWED_ORIGINS`ga o'sha manzil allaqachon qo'shilgan.
Productionda frontend'ni Django `static/` orqali bitta domendan berish CORS
sozlamalarini butunlay keraksiz qiladi.

## 5. Admin panelda ishlash

- **Yuklar** bo'limida yangi yuk qo'shasiz (`tracking_number`, mijoz, marshrut).
- Shu yuk sahifasining pastida **"Status yangilanishi"** inline jadvali bor —
  shu yerdan yangi status qo'shasiz (tayyor variant yoki "Boshqa" tanlab o'z matningizni yozasiz).
- Yuk ustidagi "joriy status" maydonlari **avtomatik** yangilanadi, qo'lda o'zgartirmang.

## 6. Model tuzilishi

```
Cargo
 ├─ tracking_number (unique)
 ├─ client_name, client_phone
 ├─ origin, destination
 ├─ current_status_category / current_status_text   ← avtomatik yangilanadi
 └─ history → CargoStatusUpdate (FK, ko'p dona)
       ├─ status_category (tayyor ro'yxatdan)
       ├─ custom_text     (faqat "Boshqa" tanlanganda)
       ├─ location, comment
       └─ created_at
```

## 7. Keyingi qadam — aiogram 2 bot

Bot va Django bir xil `Cargo` / `CargoStatusUpdate` modellaridan foydalanishi kerak.
Buning uchun eng toza yo'l — botni ham shu Django loyihasi ichida, `manage.py`
orqali ishga tushiriladigan alohida management command sifatida yozish
(`python manage.py runbot`), shunda Django ORM'ga to'g'ridan-to'g'ri, `sync_to_async`
bilan murojaat qilasiz — alohida API chaqirishga hojat qolmaydi.
