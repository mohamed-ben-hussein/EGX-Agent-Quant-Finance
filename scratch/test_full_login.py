from playwright.sync_api import sync_playwright

def test_full_login_flow():
    with sync_playwright() as p:
        browser = p.chromium.launch(executable_path=r'C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe', headless=True)
        page = browser.new_page()
        
        target_url = "https://www.mubasher.info/markets/EGX/stocks/EGX30/announcements"
        print(f"Navigating to {target_url}")
        page.goto(target_url)
        page.wait_for_timeout(5000)
        
        print(f"Current URL: {page.url}")
        if "login" in page.url.lower():
            print("Redirected to login. Filling iframe...")
            login_frame = page.frame_locator("#loginIframe")
            
            user_input = login_frame.locator("input[type='email'], input[id='mat-input-2']").first
            user_input.type("harbharb186@gmail.com", delay=100)
            
            pass_input = login_frame.locator("input[type='password'], input[id='mat-input-3']").first
            pass_input.type("123456789Mm", delay=100)
            
            login_btn = login_frame.locator("button[type='submit'], .btn-submit").first
            login_btn.click(delay=200)
            
            print("Clicked login. Waiting 5 seconds...")
            page.wait_for_timeout(5000)
            
            print(f"URL after waiting: {page.url}")
            
            print("Force navigating back to announcements...")
            page.goto(target_url)
            page.wait_for_timeout(5000)
            
            print(f"Final URL: {page.url}")
            page.screenshot(path="data/final_test_shot.png")
            print("Screenshot saved to data/final_test_shot.png")
            
        browser.close()

if __name__ == "__main__":
    test_full_login_flow()
