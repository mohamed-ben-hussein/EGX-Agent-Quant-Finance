from playwright.sync_api import sync_playwright

def find_article():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        print("Opening announcements page...")
        page.goto("https://www.mubasher.info/news/eg/now/announcements", timeout=60000)
        page.wait_for_timeout(5000)
        
        # Scroll a bit
        for _ in range(3):
            page.evaluate("window.scrollBy(0, 1000)")
            page.wait_for_timeout(1000)
            
        links = page.evaluate("() => Array.from(document.querySelectorAll('a')).map(a => a.href)")
        
        target = "4613458"
        found = [l for l in links if target in l]
        
        print(f"Total links found: {len(links)}")
        if found:
            print(f"FOUND TARGET: {found[0]}")
        else:
            print("TARGET NOT FOUND IN TOP OF LIST.")
            # Print first 20 news links for context
            news_links = [l for l in links if "/news/" in l][:20]
            for nl in news_links:
                print(f"  - {nl}")
        
        browser.close()

if __name__ == "__main__":
    find_article()
