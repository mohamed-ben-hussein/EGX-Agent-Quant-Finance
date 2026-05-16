from playwright.sync_api import sync_playwright
import re

def count_news():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        print("Navigating...")
        page.goto("https://www.mubasher.info/news/eg/now/announcements", wait_until="networkidle")
        
        print("Scrolling...")
        for _ in range(5):
            page.evaluate("window.scrollBy(0, 2000)")
            page.wait_for_timeout(2000)
            
        links = page.evaluate("() => Array.from(document.querySelectorAll('a')).map(a => a.href)")
        print(f"Total links found: {len(links)}")
        
        article_pattern = re.compile(r"/news/\d+")
        news_links = [l for u in links if (l := str(u)) and article_pattern.search(l)]
        unique_news = set(news_links)
        print(f"Unique news links found: {len(unique_news)}")
        
        target = "4613458"
        found = [u for u in unique_news if target in u]
        print(f"Found target {target} in list:", len(found) > 0)
        if found:
            print(f"Sample target URL: {found[0]}")
            
        browser.close()

if __name__ == "__main__":
    count_news()
