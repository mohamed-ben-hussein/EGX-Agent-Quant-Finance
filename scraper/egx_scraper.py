# ============================================================
#  scraper/egx_scraper.py
#  مسؤول عن: تنسيق عملية الـ scraping الكاملة
# ============================================================

import re
import logging

from scraper.browser_manager import BrowserManager
from scraper.parser          import MubasherParser
from scraper.downloader      import PDFDownloader
from scraper.storage         import DisclosureStorage

import config

log = logging.getLogger("EGXScraper")

# نمط للتعرف على صفحة مقال فردي
_ARTICLE_URL_PATTERN = re.compile(r"/news/\d+")


class EGXScraper:
    """
    المُنسِّق الرئيسي لعملية جمع إفصاحات البورصة المصرية من Mubasher.
    يدير: المتصفح ← تسجيل الدخول ← الـ scraping ← التخزين ← الـ backfill.
    """

    def __init__(self, username: str = None, password: str = None):
        """
        Args:
            username: إيميل حساب Mubasher (يُقرأ من config إن لم يُحدَّد)
            password: كلمة المرور (يُقرأ من config إن لم تُحدَّد)
        """
        self.target_url = config.SCRAPER["target_url"]
        self.username   = username or config.MUBASHER_USERNAME
        self.password   = password or config.MUBASHER_PASSWORD

        self.browser_manager = BrowserManager()
        self.storage         = DisclosureStorage()
        self.downloaded_count = 0

    # ----------------------------------------------------------
    def run(self):
        """ينفّذ دورة scraping كاملة ثم يغلق المتصفح."""
        context = self.browser_manager.start()

        try:
            page = context.new_page()
            page.add_init_script(self._stealth_script())

            log.info(f"Navigating to: {self.target_url}")
            page.goto(self.target_url, wait_until="domcontentloaded",
                      timeout=config.SCRAPER["page_timeout_ms"])

            parser     = MubasherParser(page)
            downloader = PDFDownloader(context)

            self._main_loop(page, parser, downloader)
            self._backfill_missing_pdfs(page, parser, downloader)

            stats = self.storage.get_stats()
            log.info(
                f"Run complete. DB: {stats['total']} total, "
                f"{stats['with_pdf']} with PDF. "
                f"Downloaded this run: {self.downloaded_count}"
            )

        finally:
            self.browser_manager.stop()

    # ----------------------------------------------------------
    def _main_loop(self, page, parser: MubasherParser, downloader: PDFDownloader):
        """
        الحلقة الرئيسية: تنتقل بين المقالات حتى تُعالج الكل.

        Args:
            page:       Playwright page object
            parser:     مُحلِّل HTML
            downloader: مُحمِّل PDF
        """
        session_processed: set[str] = set()
        max_attempts = config.SCRAPER["max_loop_attempts"]

        for attempt in range(max_attempts):
            page.wait_for_timeout(3_000)
            current_url = page.url.lower()

            has_logout       = page.evaluate("() => document.body.innerText.includes('خروج')")
            has_announcements = (
                "announcements" in current_url
                or page.evaluate("() => document.body.innerText.includes('إعلانات السوق')")
            )

            log.info(
                f"[{attempt + 1}/{max_attempts}] URL={current_url[:60]} "
                f"LoggedIn={has_logout} Announcements={has_announcements}"
            )

            # 1. صفحة تسجيل الدخول
            if "login" in current_url and not has_logout:
                log.info("Login page detected — attempting login...")
                if self._login(page):
                    page.wait_for_timeout(10_000)
                continue

            # 2. صفحة مقال فردي
            if _ARTICLE_URL_PATTERN.search(current_url):
                self._process_article(page, current_url, parser, downloader, session_processed)
                page.goto(self.target_url, wait_until="domcontentloaded",
                          timeout=config.SCRAPER["page_timeout_ms"])
                continue

            # 3. قائمة الإعلانات
            if has_announcements:
                next_article = self._pick_next_article(page, parser, session_processed)
                if next_article:
                    page.goto(next_article, wait_until="domcontentloaded",
                              timeout=config.SCRAPER["page_timeout_ms"])
                else:
                    log.info("All visible articles processed. Scrolling for more...")
                    page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                    page.wait_for_timeout(5_000)
                continue

            # 4. حالة غير معروفة — العودة للصفحة الرئيسية
            log.warning("Unknown state — navigating back to target...")
            page.goto(self.target_url, wait_until="domcontentloaded",
                      timeout=config.SCRAPER["page_timeout_ms"])

    # ----------------------------------------------------------
    def _process_article(
        self, page, url: str,
        parser: MubasherParser, downloader: PDFDownloader,
        session_processed: set
    ):
        """
        يعالج مقالًا واحدًا: يستخرج التفاصيل ويحمّل الـ PDF.

        Args:
            page:              Playwright page
            url:               رابط المقال الحالي
            parser:            مُحلِّل HTML
            downloader:        مُحمِّل PDF
            session_processed: مجموعة الروابط المُعالَجة في هذه الدورة
        """
        normalized = MubasherParser._normalize_url(url)
        session_processed.add(normalized)

        # تخطي إذا كان في قاعدة البيانات مع PDF
        if self.storage.article_exists(normalized) and self.storage.has_pdf(normalized):
            log.info(f"Already complete — skipping: {normalized}")
            return

        log.info(f"Processing: {normalized}")
        details = parser.extract_article_details()
        log.info(f"  Title: {details.get('title', '')[:60]}")

        # حفظ المقال بدون PDF أولًا
        self.storage.save_disclosure(
            article_url=normalized,
            title=details["title"],
            content=details["content"],
            published_at=details["date"],
        )

        # البحث عن PDF وتحميله
        pdf_links = parser.extract_pdf_links()
        if pdf_links:
            for pdf_url in pdf_links:
                pdf_path = downloader.download(pdf_url)
                if pdf_path:
                    self.storage.save_disclosure(
                        article_url=normalized,
                        title=details["title"],
                        content=details["content"],
                        pdf_url=pdf_url,
                        pdf_path=pdf_path,
                        published_at=details["date"],
                    )
                    self.downloaded_count += 1
                    log.info(f"  Saved PDF: {pdf_path}")
        else:
            log.info("  No PDF found for this article.")

    # ----------------------------------------------------------
    def _pick_next_article(
        self, page, parser: MubasherParser, session_processed: set
    ) -> str | None:
        """
        يختار أول مقال لم يُعالَج بعد من القائمة الظاهرة.

        Returns:
            رابط المقال التالي أو None إذا لم يتبق شيء
        """
        article_urls = parser.extract_article_links()
        normalized   = [MubasherParser._normalize_url(u) for u in article_urls]
        log.info(f"Found {len(normalized)} candidate articles on page.")

        for url in normalized:
            if url not in session_processed and not self.storage.article_exists(url):
                session_processed.add(url)
                return url
            log.debug(f"Skipping {url}")

        return None

    # ----------------------------------------------------------
    def _backfill_missing_pdfs(self, page, parser: MubasherParser, downloader: PDFDownloader):
        """
        يُعيد فتح المقالات التي ليس لها PDF ويحاول تحميلها مجددًا.

        Args:
            page:       Playwright page
            parser:     مُحلِّل HTML
            downloader: مُحمِّل PDF
        """
        missing = self.storage.get_articles_missing_pdf()
        log.info(f"Backfill: {len(missing)} articles missing PDFs.")

        for url in missing:
            try:
                log.info(f"Backfill: opening {url}")
                page.goto(url, wait_until="domcontentloaded",
                          timeout=config.SCRAPER["page_timeout_ms"])
                page.wait_for_timeout(5_000)

                pdf_links = parser.extract_pdf_links()
                if pdf_links:
                    details = parser.extract_article_details()
                    for pdf_url in pdf_links:
                        pdf_path = downloader.download(pdf_url)
                        if pdf_path:
                            self.storage.save_disclosure(
                                article_url=url,
                                title=details["title"],
                                content=details["content"],
                                pdf_url=pdf_url,
                                pdf_path=pdf_path,
                                published_at=details["date"],
                            )
                            self.downloaded_count += 1
                            log.info(f"Backfill success: {pdf_path}")
                else:
                    log.info(f"Backfill: still no PDF found for {url}")

            except Exception as e:
                log.error(f"Backfill failed for {url}: {e}")

    # ----------------------------------------------------------
    def _login(self, page) -> bool:
        """
        يملأ نموذج تسجيل الدخول ويضغط Enter.

        Returns:
            True إذا نجح تقديم النموذج
        """
        try:
            log.info(f"Logging in as: {self.username}")
            frame = page.frame_locator("#loginIframe")
            frame.locator("input").first.wait_for(timeout=20_000)

            email_input = frame.locator("input[type='email'], input[id='mat-input-2']").first
            email_input.type(self.username, delay=100)

            pass_input = frame.locator("input[type='password'], input[id='mat-input-3']").first
            pass_input.type(self.password, delay=100)

            page.wait_for_timeout(1_000)
            pass_input.press("Enter")
            log.info("Login form submitted.")
            return True

        except Exception as e:
            log.error(f"Login failed: {e}")
            return False

    # ----------------------------------------------------------
    @staticmethod
    def _stealth_script() -> str:
        """يُرجع سكريبت JavaScript لإخفاء علامات الأتمتة عن المتصفح."""
        return """
            Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
            window.chrome = { runtime: {} };
            const proto = navigator.__proto__;
            delete proto.webdriver;
            navigator.__proto__ = proto;
        """