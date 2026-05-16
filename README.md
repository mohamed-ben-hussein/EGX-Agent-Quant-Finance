# EGX-Agent — Mubasher Disclosure Radar 🇪🇬

نظام تلقائي لجمع وتخزين الإفصاحات المالية من البورصة المصرية عبر منصة Mubasher.

---

## 📁 هيكل المشروع

```
EGX-Agent/
├── main.py              # نقطة الدخول — يشغّل الـ scraper في حلقة مستمرة
├── run_overnight.py     # مُشغِّل الليل — يشغّل main.py كـ subprocess
├── config.py            # جميع الإعدادات والمسارات (لا قيم مُدمَّجة في الكود)
├── requirements.txt     # المكتبات المطلوبة
├── .env.example         # قالب متغيرات البيئة (انسخه إلى .env)
│
├── scraper/
│   ├── browser_manager.py   # إدارة Brave Browser عبر Playwright CDP
│   ├── egx_scraper.py       # المُنسِّق الرئيسي لعملية الـ scraping
│   ├── parser.py            # استخراج البيانات من HTML
│   ├── downloader.py        # تحميل والتحقق من ملفات PDF
│   └── storage.py           # طبقة قاعدة البيانات SQLite
│
├── data/
│   ├── egx.db           # قاعدة البيانات (gitignored)
│   └── pdfs/            # ملفات PDF المُحمَّلة (gitignored)
│
└── logs/                # ملفات اللوق (gitignored)
```

---

## ⚙️ الإعداد والتشغيل

### 1. تثبيت المكتبات

```bash
pip install -r requirements.txt
playwright install chromium
```

### 2. إعداد بيانات الدخول

```bash
copy .env.example .env
```

ثم افتح ملف `.env` وضع بيانات حسابك على Mubasher:

```env
MUBASHER_USERNAME=your_email@example.com
MUBASHER_PASSWORD=your_password_here
```

### 3. التشغيل

```bash
# تشغيل عادي (حلقة مستمرة)
python main.py

# تشغيل ليلي (subprocess مستقل مع لوق منفصل)
python run_overnight.py
```

---

## 🗄️ قاعدة البيانات

جدول `disclosures` يخزن:

| العمود | الوصف |
|--------|-------|
| `article_url` | رابط المقال (مفتاح فريد) |
| `title` | عنوان الإفصاح |
| `content` | النص الكامل للمقال |
| `pdf_url` | رابط ملف PDF الإفصاح |
| `pdf_path` | المسار المحلي للـ PDF |
| `published_at` | تاريخ النشر |
| `scraped_at` | وقت الحفظ في قاعدة البيانات |

---

## ⚙️ الإعدادات (`config.py`)

جميع الإعدادات مركزية في `config.py`:

- **`SCRAPER["cycle_interval"]`** — الفترة بين كل دورة (افتراضي: 300 ثانية)
- **`SCRAPER["scroll_rounds"]`** — عدد مرات التمرير لتحميل المقالات (افتراضي: 15)
- **`SCRAPER["max_retries"]`** — عدد محاولات إعادة تحميل PDF (افتراضي: 3)
- **`DB_PATH`** — مسار قاعدة البيانات
- **`PDF_DIR`** — مجلد تخزين ملفات PDF

---

## 🔒 الأمان

- **لا تُضِف `.env` أو `user_data.py` إلى git أبدًا**
- ملف `.gitignore` يحمي: `.env`، `user_data.py`، `brave_session/`، `logs/`، `data/*.html`

---

## 📊 الحالة الحالية

- [x] Brave browser integration via CDP
- [x] تسجيل دخول تلقائي
- [x] تحميل PDF مع التحقق من Magic Bytes
- [x] إعادة المحاولة مع Exponential Backoff
- [x] Backfill للمقالات التي فاتها PDF
- [x] لوق منظم إلى ملف وconsole
- [ ] استخراج نص PDF تلقائيًا
- [ ] ربط الإفصاحات بالشركات (company_id)
- [ ] جدول بيانات الأسعار التاريخية
