# scraper/storage.py

import sqlite3
from pathlib import Path


class DisclosureStorage:
    def __init__(self, db_path="data/egx.db"):
        Path("data").mkdir(exist_ok=True)

        self.conn = sqlite3.connect(db_path)
        self._create_tables()

    def _create_tables(self):
        self.conn.execute("""
        CREATE TABLE IF NOT EXISTS disclosures (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            article_url TEXT UNIQUE,
            title TEXT,
            content TEXT,
            pdf_url TEXT,
            pdf_path TEXT,
            published_at TEXT,
            scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)

        self.conn.commit()

    def disclosure_exists(self, pdf_url):
        cursor = self.conn.execute(
            "SELECT id FROM disclosures WHERE pdf_url = ?",
            (pdf_url,)
        )

        return cursor.fetchone() is not None

    def article_exists(self, article_url):
        cursor = self.conn.execute(
            "SELECT id FROM disclosures WHERE article_url = ?",
            (article_url,)
        )
        return cursor.fetchone() is not None

    def has_pdf(self, article_url):
        cursor = self.conn.execute(
            "SELECT id FROM disclosures WHERE article_url = ? AND pdf_url IS NOT NULL",
            (article_url,)
        )
        return cursor.fetchone() is not None

    def save_disclosure(self, article_url, title, content, pdf_url=None, pdf_path=None, published_at=None):
        self.conn.execute("""
        INSERT OR IGNORE INTO disclosures
        (article_url, title, content, pdf_url, pdf_path, published_at)
        VALUES (?, ?, ?, ?, ?, ?)
        """, (article_url, title, content, pdf_url, pdf_path, published_at))
        
        # If record already exists but we found a PDF later, update it
        if pdf_url:
            self.conn.execute("""
            UPDATE disclosures SET pdf_url = ?, pdf_path = ? 
            WHERE article_url = ? AND (pdf_url IS NULL OR pdf_url = '')
            """, (pdf_url, pdf_path, article_url))

        self.conn.commit()

    def get_articles_missing_pdf(self):
        cursor = self.conn.execute(
            "SELECT article_url FROM disclosures WHERE pdf_url IS NULL OR pdf_url = ''"
        )
        return [row[0] for row in cursor.fetchall()]