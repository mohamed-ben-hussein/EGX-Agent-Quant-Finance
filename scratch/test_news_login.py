from playwright.sync_api import sync_playwright

def test_enter_login_news():
    with sync_playwright() as p:
        browser = p.chromium.launch(executable_path=r'C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe', headless=True)
        page = browser.new_page()
        
        # Target the tricky meeting minutes article
        target_url = "https://www.mubasher.info/news/4613458"
        print(f"Navigating to {target_url}")
        page.goto(target_url, wait_until="domcontentloaded", timeout=60000)
        page.wait_for_timeout(10000)
        
        print(f"Current URL: {page.url}")
        
        print("Waiting 15 seconds for dynamic content...")
        page.wait_for_timeout(15000)
        
        with open("data/announcements_dump.html", "w", encoding="utf-8") as f:
            f.write(page.content())
        print("HTML dump saved to data/announcements_dump.html")
        
        browser.close()

if __name__ == "__main__":
    test_enter_login_news()
