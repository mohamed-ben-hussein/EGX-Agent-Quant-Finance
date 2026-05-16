# ============================================================
#  EGX-Agent — Centralized Configuration
#  جميع الإعدادات في مكان واحد، لا قيم مُدمجة في الكود
# ============================================================

import os
from pathlib import Path
from dotenv import load_dotenv

# --- تحميل .env إن وُجد ---
load_dotenv()

# ============================================================
#  المسارات الأساسية
# ============================================================

# جذر المشروع
BASE_DIR = Path(__file__).parent.resolve()

# مجلد البيانات
DATA_DIR = BASE_DIR / "data"
PDF_DIR  = DATA_DIR / "pdfs"
LOG_DIR  = BASE_DIR / "logs"

# قاعدة البيانات
DB_PATH  = DATA_DIR / "egx.db"

# مجلد جلسة المتصفح (خارج الـ git)
BRAVE_SESSION_DIR = BASE_DIR / "brave_session"

# ============================================================
#  بيانات الدخول (محمية في .env)
# ============================================================

MUBASHER_USERNAME: str = os.getenv("MUBASHER_USERNAME", "")
MUBASHER_PASSWORD: str = os.getenv("MUBASHER_PASSWORD", "")

# ============================================================
#  إعدادات الـ Scraper
# ============================================================

SCRAPER = {
    # رابط صفحة الإعلانات الرئيسي
    "target_url": "https://www.mubasher.info/news/eg/now/announcements",

    # بورت الـ CDP لـ Brave
    "debugging_port": 9222,

    # timeout لتحميل الصفحة (ميلي ثانية)
    "page_timeout_ms": 60_000,

    # عدد مرات إعادة المحاولة عند الفشل
    "max_retries": 3,

    # الانتظار الأساسي بين المحاولات (ثانية) — يتضاعف مع كل محاولة
    "retry_base_delay": 2.0,

    # عدد دورات التمرير لتحميل المزيد من المقالات
    "scroll_rounds": 15,

    # الانتظار بين دورات الـ Scraping الكاملة (ثانية)
    "cycle_interval": 300,

    # الحد الأقصى للمحاولات داخل كل دورة
    "max_loop_attempts": 100,
}

# ============================================================
#  إعدادات اللوق
# ============================================================

LOGGING = {
    "level": "INFO",
    "format": "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    "log_file": str(LOG_DIR / "scraper.log"),
    "encoding": "utf-8",
}

# ============================================================
#  إنشاء المجلدات المطلوبة تلقائيًا
# ============================================================

for _dir in [DATA_DIR, PDF_DIR, LOG_DIR, BRAVE_SESSION_DIR]:
    _dir.mkdir(parents=True, exist_ok=True)
