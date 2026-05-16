# scraper/parser.py

from urllib.parse import urljoin


class MubasherParser:
    def __init__(self, page):
        self.page = page

    def extract_article_details(self):
        """Extracts the full title, content and date from a news article page."""
        details = self.page.evaluate("""() => {
            const title = document.querySelector('h1.mi-article__headline')?.innerText || '';
            const content = document.querySelector('.mi-article__body, .mi-article__content')?.innerText || '';
            const date = document.querySelector('.mi-article__date')?.innerText || '';
            return { title, content, date };
        }""")
        return details

    def extract_article_links(self):
        # Wait for lazy loading and scroll to get more articles
        import logging
        import re
        logger = logging.getLogger("Parser")
        article_pattern = re.compile(r"/news/\d+")
        all_article_urls = set()
        
        for i in range(15): 
            logger.info(f"Scrolling page to load more articles ({i+1}/15)...")
            
            # Extract current links BEFORE scrolling more
            links = self.page.evaluate("() => Array.from(document.querySelectorAll('a')).map(a => a.href)")
            logger.info(f"  Step {i+1}: Found {len(links)} total links on page.")
            for href in links:
                if href and article_pattern.search(href):
                    clean_href = href.rstrip('/').replace('//news', '/news')
                    all_article_urls.add(clean_href)
            
            # Use multiple scroll methods to be sure
            self.page.keyboard.press("End")
            self.page.mouse.wheel(0, 2000)
            self.page.wait_for_timeout(2000) 
            
        logger.info(f"Total unique article links captured during progressive scrolling: {len(all_article_urls)}")
        return list(all_article_urls)

    def extract_pdf_links(self):
        # Wait even longer for article content and external links to load
        self.page.wait_for_timeout(15000)
        
        # Get all links, including those that might be plain text or in shadow DOM
        # Robust Search: Use regex on full page content to find ANY PDF links
        import re
        import logging
        logger = logging.getLogger("Parser-PDF")
        
        pdf_links = set()
        
        # Check main frame + all child frames
        try:
            main_content = self.page.content()
            all_frames_content = [main_content]
            logger.info(f"Main frame content length: {len(main_content)}")
        except Exception as e:
            logger.error(f"Could not get main frame content: {e}")
            all_frames_content = [""]
        
        for i, frame in enumerate(self.page.frames[1:]):
            try:
                # Wait a bit for frame content to stabilize
                c = frame.content()
                all_frames_content.append(c)
                logger.info(f"Frame {i+1} content length: {len(c)}")
            except Exception as e:
                logger.debug(f"Could not get content of frame {i+1}: {e}")
        
        # Aggressive PDF pattern: look for anything that looks like a URL ending in .pdf
        # or even just a filename ending in .pdf within text
        pdf_pattern = re.compile(r'https?://[^\s"\'<>)]+\.pdf|[^\s"\'<>/]+\.pdf', re.IGNORECASE)
        
        for content in all_frames_content:
            found_matches = pdf_pattern.findall(content)
            for match in found_matches:
                # Clean match
                clean_match = match.strip().strip('()[]{},;')
                
                # If it's just a filename, join it with base URL
                if not clean_match.startswith("http"):
                    # Try to see if it's a relative path or just a filename
                    full_url = urljoin(self.page.url, clean_match)
                else:
                    full_url = clean_match
                
                if full_url not in pdf_links:
                    logger.info(f"ROBUST PDF MATCH: {full_url}")
                    pdf_links.add(full_url)

        # Final check: look for any elements with 'pdf' in their ID or class that might be clickable
        # but let's stick to URL extraction for now as it's more reliable for downloads.
        
        return list(pdf_links)