# scraper/downloader.py

import logging
from pathlib import Path
from urllib.parse import urlparse

log = logging.getLogger("Downloader")


class PDFDownloader:
    def __init__(self, context, download_dir="data/pdfs"):
        self.context = context

        self.download_dir = Path(download_dir)
        self.download_dir.mkdir(parents=True, exist_ok=True)

    def download_pdf(self, pdf_url):
        try:
            filename = Path(urlparse(pdf_url).path).name
            if not filename.endswith(".pdf"):
                filename += ".pdf"
            filepath = self.download_dir / filename

            # Try Playwright first
            try:
                response = self.context.request.get(pdf_url, timeout=30000)
                if response.ok:
                    content = response.body()
                    if content.startswith(b"%PDF"):
                        filepath.write_bytes(content)
                        log.info(f"Downloaded (Playwright): {filename}")
                        return str(filepath)
            except Exception as e:
                log.warning(f"Playwright download failed, trying requests fallback: {e}")

            # Fallback to requests for tricky EGX redirects/SSL issues
            import requests
            import urllib3
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
            
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
                "Accept-Language": "en-US,en;q=0.9,ar;q=0.8",
                "Referer": "https://www.mubasher.info/"
            }
            # Verify=False to handle potential SSL issues on EGX site
            resp = requests.get(pdf_url, headers=headers, timeout=30, verify=False, allow_redirects=True)
            if resp.status_code == 200:
                content = resp.content
                if b"%PDF" in content[:1024]:
                    filepath.write_bytes(content)
                    log.info(f"Downloaded (Requests): {filename}")
                    return str(filepath)
                else:
                    log.warning(f"Downloaded content is not a PDF: {content[:10]}")
            else:
                log.error(f"Requests download failed with status {resp.status_code}")

        except Exception as e:
            log.error(f"Fatal error during PDF download: {e}")

        return None