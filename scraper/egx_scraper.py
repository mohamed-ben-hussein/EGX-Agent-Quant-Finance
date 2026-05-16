# scraper/egx_scraper.py

import logging
import re
from pathlib import Path

from scraper.browser_manager import BrowserManager
from scraper.parser import MubasherParser
from scraper.downloader import PDFDownloader
from scraper.storage import DisclosureStorage

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)

log = logging.getLogger("EGXScraper")

# Setup File Logging
log_dir = Path("logs")
log_dir.mkdir(exist_ok=True)
file_handler = logging.FileHandler(log_dir / "scraper.log", encoding="utf-8")
file_handler.setFormatter(logging.Formatter('%(asctime)s [%(levelname)s] %(name)s: %(message)s'))
logging.getLogger().addHandler(file_handler)


class EGXScraper:
    def __init__(self, username=None, password=None):
        self.base_url = "https://www.mubasher.info/news/eg/now/announcements"
        self.username = username
        self.password = password

        self.browser_manager = BrowserManager()
        self.storage = DisclosureStorage()

        self.downloaded_count = 0

    def run(self):
        context = self.browser_manager.start()

        try:
            page = context.new_page()
            
            # Ultra Stealth Script for Brave
            stealth_script = """
            Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
            window.chrome = { runtime: {} };
            const newProto = navigator.__proto__;
            delete newProto.webdriver;
            navigator.__proto__ = newProto;
            """
            page.add_init_script(stealth_script)

            target_url = self.base_url
            
            log.info(f"Opening Target URL: {target_url}")
            page.goto(target_url, wait_until="domcontentloaded", timeout=60000)
            
            parser = MubasherParser(page)
            downloader = PDFDownloader(context)
            
            # Smart Navigation & Automated Login Loop
            session_processed = set()
            max_retries = 100
            for attempt in range(max_retries):
                page.wait_for_timeout(3000)
                current_url = page.url.lower()
                
                # Check for logged-in state or content first
                has_logout = page.evaluate("() => document.body.innerText.includes('خروج')")
                has_announcements = "announcements" in current_url or page.evaluate("() => document.body.innerText.includes('إعلانات السوق')")
                
                log.info(f"State: URL={current_url}, LoggedIn={has_logout}, AnnouncementsVisible={has_announcements}")

                # 1. Login Handling
                if "login" in current_url and not has_logout and not has_announcements:
                    log.info("Login page detected. Attempting AUTOMATED LOGIN...")
                    if self._login(page):
                        log.info("Login form submitted. Waiting for redirect...")
                        page.wait_for_timeout(10000)
                    continue
                
                # 2. Article Page Handling
                if re.search(r"/news/\d+", current_url):
                    log.info(f"Inside Article Page: {current_url}")
                    
                    # Normalize current_url for DB check
                    normalized_url = current_url.rstrip('/').replace('//news', '/news')
                    session_processed.add(normalized_url)
                    
                    has_pdf_in_db = self.storage.has_pdf(normalized_url)
                    
                    if self.storage.article_exists(normalized_url) and has_pdf_in_db:
                        log.info(f"Article and PDF already in database: {normalized_url}")
                    else:
                        log.info(f"Processing article (New or missing PDF): {normalized_url}")
                        # Extract ALL details (Title, Content, Date)
                        details = parser.extract_article_details()
                        log.info(f"Extracted Article: {details['title']}")
                        
                        # Save initially without PDF
                        self.storage.save_disclosure(
                            article_url=normalized_url,
                            title=details['title'],
                            content=details['content'],
                            published_at=details['date']
                        )
                        
                        # Now look for PDFs
                        pdf_links = parser.extract_pdf_links()
                        if pdf_links:
                            for pdf_url in pdf_links:
                                pdf_path = downloader.download_pdf(pdf_url)
                                if pdf_path:
                                    self.storage.save_disclosure(
                                        article_url=normalized_url,
                                        title=details['title'],
                                        content=details['content'],
                                        pdf_url=pdf_url,
                                        pdf_path=pdf_path,
                                        published_at=details['date']
                                    )
                                    self.downloaded_count += 1
                                    log.info(f"SUCCESS: Saved PDF {pdf_path}")
                        else:
                            log.info("No disclosure PDF links found, but article text saved.")
                    
                    # Return to list
                    log.info("Returning to announcements list...")
                    page.goto(target_url, wait_until="domcontentloaded", timeout=60000)
                    continue
                
                # 3. Announcements List Handling
                if has_announcements or "announcements" in current_url:
                    log.info("Announcements list detected or visible.")
                    article_urls = parser.extract_article_links()
                    
                    def normalize(u):
                        return u.rstrip('/').replace('//news', '/news')
                        
                    # Use parser output directly
                    raw_urls = [normalize(u) for u in article_urls]
                    log.info(f"Total candidate articles for processing: {len(raw_urls)}")
                    for i, u in enumerate(raw_urls):
                        log.info(f"  Candidate {i+1}: {u}")
                    
                    # Find first unvisited and un-scraped article
                    next_article = None
                    for url in raw_urls:
                        is_processed = url in session_processed
                        is_in_db = self.storage.article_exists(url)
                        
                        if not is_processed and not is_in_db:
                            next_article = url
                            session_processed.add(url)
                            break
                        else:
                            log.info(f"Skipping {url}: processed={is_processed}, in_db={is_in_db}")
                    
                    if next_article:
                        log.info(f"Opening next article: {next_article}")
                        page.goto(next_article, wait_until="domcontentloaded", timeout=60000)
                    else:
                        log.info("All visible articles processed or already in DB. Scrolling for more...")
                        page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                        page.wait_for_timeout(5000)
                else:
                    log.info("Lost or Redirected. Navigating back to announcements...")
                    page.goto(target_url, wait_until="domcontentloaded", timeout=60000)

            # 4. Backfill Missing PDFs
            self.backfill_missing_pdfs(page, parser, downloader)

            log.info(f"Run completed. Total PDFs downloaded: {self.downloaded_count}")

        finally:
            self.browser_manager.stop()

    def backfill_missing_pdfs(self, page, parser, downloader):
        log.info("Starting BACKFILL for articles missing PDFs...")
        missing_urls = self.storage.get_articles_missing_pdf()
        log.info(f"Found {len(missing_urls)} articles missing PDFs.")
        
        for url in missing_urls:
            try:
                log.info(f"BACKFILL: Opening {url}")
                page.goto(url, wait_until="domcontentloaded", timeout=60000)
                page.wait_for_timeout(5000) # Give it time to load content
                
                # Robust extraction
                pdf_links = parser.extract_pdf_links()
                if pdf_links:
                    # Get article details to ensure we have title etc (though already in DB)
                    details = parser.extract_article_details()
                    for pdf_url in pdf_links:
                        pdf_path = downloader.download_pdf(pdf_url)
                        if pdf_path:
                            self.storage.save_disclosure(
                                article_url=url,
                                title=details['title'],
                                content=details['content'],
                                pdf_url=pdf_url,
                                pdf_path=pdf_path,
                                published_at=details['date']
                            )
                            self.downloaded_count += 1
                            log.info(f"BACKFILL SUCCESS: Saved PDF {pdf_path} for {url}")
                else:
                    log.info(f"BACKFILL: Still no PDF found for {url}")
            except Exception as e:
                log.error(f"BACKFILL FAILED for {url}: {e}")

    def _login(self, page):
        try:
            log.info(f"Logging in as {self.username}...")
            login_frame = page.frame_locator("#loginIframe")
            login_frame.locator("input").first.wait_for(timeout=20000)
            
            user_input = login_frame.locator("input[type='email'], input[id='mat-input-2']").first
            user_input.type(self.username, delay=100)
            
            pass_input = login_frame.locator("input[type='password'], input[id='mat-input-3']").first
            pass_input.type(self.password, delay=100)
            
            page.wait_for_timeout(1000)
            pass_input.press("Enter")
            log.info("Login submitted via Enter.")
            
            return True
        except Exception as e:
            log.error(f"Login failed: {e}")
            return False