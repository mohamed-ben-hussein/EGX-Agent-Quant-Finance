# ============================================================
#  scraper/downloader.py
#  مسؤول عن: تحميل ملفات PDF والتحقق من صحتها
# ============================================================

import logging
import time
import random
from pathlib import Path
from urllib.parse import urlparse

import requests
import urllib3

import config

# إيقاف تحذيرات SSL لأن بعض روابط EGX تستخدم شهادات قديمة
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

log = logging.getLogger("Downloader")

# Magic bytes التي يبدأ بها كل ملف PDF صحيح
_PDF_MAGIC = b"%PDF-"

# حجم أدنى مقبول للملف (1 KB) — ما دون ذلك يعتبر خطأ
_MIN_FILE_SIZE = 1_024


class PDFDownloader:
    """
    يحمّل ملفات PDF من روابطها ويتحقق من صحتها.
    يحاول أولًا عبر Playwright ثم يتراجع لـ requests عند الفشل.
    """

    def __init__(self, context):
        """
        Args:
            context: Playwright BrowserContext لإعادة استخدام كوكيز الجلسة
        """
        self.context     = context
        self.download_dir = config.PDF_DIR
        self.max_retries  = config.SCRAPER["max_retries"]
        self.base_delay   = config.SCRAPER["retry_base_delay"]

        self._headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            ),
            "Accept": (
                "text/html,application/xhtml+xml,application/xml;"
                "q=0.9,image/avif,image/webp,*/*;q=0.8"
            ),
            "Accept-Language": "en-US,en;q=0.9,ar;q=0.8",
            "Referer":         "https://www.mubasher.info/",
        }

    # ----------------------------------------------------------
    def download(self, pdf_url: str) -> str | None:
        """
        يحاول تحميل PDF مع إعادة المحاولة عند الفشل.

        Args:
            pdf_url: رابط ملف الـ PDF

        Returns:
            المسار المحلي للملف إذا نجح التحميل، أو None عند الفشل
        """
        for attempt in range(1, self.max_retries + 1):
            result = self._try_download(pdf_url)
            if result:
                return result

            # Exponential backoff مع Jitter عشوائي
            if attempt < self.max_retries:
                delay = self.base_delay * (2 ** (attempt - 1)) + random.uniform(0, 1)
                log.warning(f"Attempt {attempt} failed. Retrying in {delay:.1f}s...")
                time.sleep(delay)

        log.error(f"All {self.max_retries} attempts failed for: {pdf_url}")
        return None

    # ----------------------------------------------------------
    def _try_download(self, pdf_url: str) -> str | None:
        """محاولة تحميل واحدة: Playwright أولًا ثم requests."""

        filepath = self._build_filepath(pdf_url)

        # إذا كان الملف محمّلًا بالفعل، لا نعيد التحميل
        if filepath.exists() and filepath.stat().st_size > _MIN_FILE_SIZE:
            log.info(f"File already exists, skipping: {filepath.name}")
            return str(filepath)

        # --- المحاولة الأولى: Playwright (يستخدم كوكيز الجلسة) ---
        try:
            response = self.context.request.get(pdf_url, timeout=30_000)
            if response.ok:
                content = response.body()
                if self._is_valid_pdf(content):
                    filepath.write_bytes(content)
                    log.info(f"[Playwright] Downloaded: {filepath.name} ({len(content):,} bytes)")
                    return str(filepath)
                log.warning(f"[Playwright] Content is not a valid PDF: {content[:16]}")
        except Exception as e:
            log.warning(f"[Playwright] Request failed: {e}")

        # --- المحاولة الثانية: requests (يتجاوز بعض قيود الـ CDN) ---
        try:
            resp = requests.get(
                pdf_url, headers=self._headers,
                timeout=30, verify=False, allow_redirects=True
            )
            if resp.status_code == 200:
                content = resp.content
                if self._is_valid_pdf(content):
                    filepath.write_bytes(content)
                    log.info(f"[requests] Downloaded: {filepath.name} ({len(content):,} bytes)")
                    return str(filepath)
                log.warning(f"[requests] Content is not a valid PDF: {content[:16]}")
            else:
                log.warning(f"[requests] HTTP {resp.status_code} for: {pdf_url}")
        except Exception as e:
            log.warning(f"[requests] Request failed: {e}")

        return None

    # ----------------------------------------------------------
    def _build_filepath(self, pdf_url: str) -> Path:
        """يبني مسار الملف المحلي من رابط الـ PDF."""
        name = Path(urlparse(pdf_url).path).name
        if not name.lower().endswith(".pdf"):
            name += ".pdf"
        return self.download_dir / name

    # ----------------------------------------------------------
    @staticmethod
    def _is_valid_pdf(content: bytes) -> bool:
        """
        يتحقق من صحة ملف PDF عبر Magic Bytes والحجم الأدنى.

        Args:
            content: محتوى الملف كـ bytes

        Returns:
            True إذا كان الملف PDF صحيحًا
        """
        return (
            len(content) > _MIN_FILE_SIZE
            and content[:5] == _PDF_MAGIC
        )