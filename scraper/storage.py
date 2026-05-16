# ============================================================
#  scraper/storage.py
#  مسؤول عن: كل العمليات مع قاعدة البيانات SQLite
# ============================================================

import sqlite3
import logging
from pathlib import Path

import config

log = logging.getLogger("Storage")


class DisclosureStorage:
    """
    طبقة الوصول إلى قاعدة البيانات.
    تدير جدول disclosures الذي يخزن الإفصاحات والـ PDF.
    """

    def __init__(self, db_path: str = None):
        # استخدم مسار config إن لم يُحدَّد مسار صريح
        resolved = Path(db_path) if db_path else config.DB_PATH
        resolved.parent.mkdir(parents=True, exist_ok=True)

        self.conn = sqlite3.connect(str(resolved))
        self.conn.row_factory = sqlite3.Row  # نتائج تُقرأ كـ dict
        self._create_tables()
        log.info(f"Database connected: {resolved}")

    # ----------------------------------------------------------
    def _create_tables(self):
        """ينشئ الجداول إن لم تكن موجودة."""
        self.conn.executescript("""
            CREATE TABLE IF NOT EXISTS disclosures (
                id           INTEGER PRIMARY KEY AUTOINCREMENT,
                article_url  TEXT    UNIQUE NOT NULL,
                title        TEXT,
                content      TEXT,
                pdf_url      TEXT,
                pdf_path     TEXT,
                published_at TEXT,
                scraped_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE INDEX IF NOT EXISTS idx_disclosures_pdf_url
                ON disclosures (pdf_url);

            CREATE INDEX IF NOT EXISTS idx_disclosures_published_at
                ON disclosures (published_at);
        """)
        self.conn.commit()

    # ----------------------------------------------------------
    def article_exists(self, article_url: str) -> bool:
        """يتحقق إذا كان المقال محفوظًا في قاعدة البيانات."""
        row = self.conn.execute(
            "SELECT id FROM disclosures WHERE article_url = ?",
            (article_url,)
        ).fetchone()
        return row is not None

    # ----------------------------------------------------------
    def has_pdf(self, article_url: str) -> bool:
        """يتحقق إذا كان للمقال ملف PDF مرتبط."""
        row = self.conn.execute(
            "SELECT id FROM disclosures WHERE article_url = ? AND pdf_url IS NOT NULL",
            (article_url,)
        ).fetchone()
        return row is not None

    # ----------------------------------------------------------
    def save_disclosure(
        self,
        article_url:  str,
        title:        str  = None,
        content:      str  = None,
        pdf_url:      str  = None,
        pdf_path:     str  = None,
        published_at: str  = None,
    ):
        """
        يحفظ إفصاحًا جديدًا أو يحدّث الـ PDF في سجل موجود.

        Args:
            article_url:  رابط مقال الإفصاح (المفتاح الفريد)
            title:        عنوان الإفصاح
            content:      النص الكامل
            pdf_url:      رابط ملف الـ PDF
            pdf_path:     المسار المحلي للملف المحمَّل
            published_at: تاريخ النشر الأصلي
        """
        self.conn.execute("""
            INSERT OR IGNORE INTO disclosures
                (article_url, title, content, pdf_url, pdf_path, published_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (article_url, title, content, pdf_url, pdf_path, published_at))

        # إذا وُجد السجل بالفعل لكنه بدون PDF، نحدّثه
        if pdf_url:
            self.conn.execute("""
                UPDATE disclosures
                   SET pdf_url = ?, pdf_path = ?
                 WHERE article_url = ?
                   AND (pdf_url IS NULL OR pdf_url = '')
            """, (pdf_url, pdf_path, article_url))

        self.conn.commit()

    # ----------------------------------------------------------
    def get_articles_missing_pdf(self) -> list[str]:
        """يُرجع قائمة روابط المقالات التي ليس لها PDF بعد."""
        rows = self.conn.execute(
            "SELECT article_url FROM disclosures WHERE pdf_url IS NULL OR pdf_url = ''"
        ).fetchall()
        return [row["article_url"] for row in rows]

    # ----------------------------------------------------------
    def get_stats(self) -> dict:
        """يُرجع إحصائيات سريعة عن قاعدة البيانات."""
        total = self.conn.execute("SELECT COUNT(*) FROM disclosures").fetchone()[0]
        with_pdf = self.conn.execute(
            "SELECT COUNT(*) FROM disclosures WHERE pdf_url IS NOT NULL"
        ).fetchone()[0]
        return {"total": total, "with_pdf": with_pdf, "missing_pdf": total - with_pdf}