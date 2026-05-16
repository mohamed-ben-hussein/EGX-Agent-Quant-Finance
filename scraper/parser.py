# ============================================================
#  scraper/parser.py
#  مسؤول عن: استخراج البيانات من صفحات Mubasher HTML
# ============================================================

import re
import logging
from urllib.parse import urljoin

log = logging.getLogger("Parser")

# نمط للتعرف على روابط المقالات (مثل /news/4613458)
_ARTICLE_PATTERN = re.compile(r"/news/\d+")

# نمط للبحث عن روابط PDF في محتوى الصفحة
_PDF_PATTERN = re.compile(
    r"https?://[^\s\"'<>)]+\.pdf|[^\s\"'<>/]+\.pdf",
    re.IGNORECASE
)


class MubasherParser:
    """
    يستخرج البيانات المنظمة من صفحات موقع Mubasher.
    يعمل مع Playwright Page object.
    """

    def __init__(self, page):
        """
        Args:
            page: Playwright Page object
        """
        self.page = page

    # ----------------------------------------------------------
    def extract_article_details(self) -> dict:
        """
        يستخرج العنوان والمحتوى والتاريخ من صفحة مقال.

        Returns:
            dict بمفاتيح: title, content, date
        """
        details = self.page.evaluate("""() => {
            const title   = document.querySelector('h1.mi-article__headline')?.innerText   || '';
            const content = document.querySelector(
                '.mi-article__body, .mi-article__content'
            )?.innerText || '';
            const date    = document.querySelector('.mi-article__date')?.innerText || '';
            return { title, content, date };
        }""")
        return details

    # ----------------------------------------------------------
    def extract_article_links(self) -> list[str]:
        """
        يمرر الصفحة تدريجيًا لتحميل المقالات ثم يجمع كل روابط الأخبار.

        Returns:
            قائمة بروابط المقالات الفريدة (مُنظَّفة)
        """
        from config import SCRAPER
        scroll_rounds = SCRAPER["scroll_rounds"]
        all_urls: set[str] = set()

        for i in range(scroll_rounds):
            log.info(f"Scroll {i + 1}/{scroll_rounds}: collecting links...")

            links = self.page.evaluate(
                "() => Array.from(document.querySelectorAll('a')).map(a => a.href)"
            )
            for href in links:
                if href and _ARTICLE_PATTERN.search(href):
                    all_urls.add(self._normalize_url(href))

            # التمرير بأساليب متعددة لضمان تحميل المزيد
            self.page.keyboard.press("End")
            self.page.mouse.wheel(0, 2_000)
            self.page.wait_for_timeout(2_000)

        log.info(f"Total unique article links found: {len(all_urls)}")
        return list(all_urls)

    # ----------------------------------------------------------
    def extract_pdf_links(self) -> list[str]:
        """
        يبحث عن روابط PDF في الصفحة الحالية وجميع frames أبنائها.
        يستخدم Regex على محتوى HTML الكامل.

        Returns:
            قائمة بروابط PDF الفريدة
        """
        # انتظر لتحميل المحتوى المتأخر (lazy-loaded)
        self.page.wait_for_timeout(15_000)

        pdf_links: set[str] = set()

        # اجمع محتوى الـ frame الرئيسي وكل الـ frames الأبناء
        contents = self._collect_all_frame_contents()

        for content in contents:
            for match in _PDF_PATTERN.findall(content):
                clean = match.strip().strip("()[]{},;")
                # روابط نسبية → مطلقة
                full_url = (
                    clean if clean.startswith("http")
                    else urljoin(self.page.url, clean)
                )
                if full_url not in pdf_links:
                    log.info(f"PDF found: {full_url}")
                    pdf_links.add(full_url)

        return list(pdf_links)

    # ----------------------------------------------------------
    def _collect_all_frame_contents(self) -> list[str]:
        """يجمع HTML content من الـ frame الرئيسي وكل الـ frames."""
        contents = []
        try:
            contents.append(self.page.content())
        except Exception as e:
            log.error(f"Could not read main frame: {e}")

        for i, frame in enumerate(self.page.frames[1:], start=1):
            try:
                contents.append(frame.content())
            except Exception as e:
                log.debug(f"Could not read frame {i}: {e}")

        return contents

    # ----------------------------------------------------------
    @staticmethod
    def _normalize_url(url: str) -> str:
        """يُنظِّف الرابط: يزيل الـ trailing slash ويصحح التكرار."""
        return url.rstrip("/").replace("//news", "/news")