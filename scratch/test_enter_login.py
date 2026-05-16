from playwright.sync_api import sync_playwright

def test_enter_login():
    with sync_playwright() as p:
        browser = p.chromium.launch(executable_path=r'C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe', headless=True)
        page = browser.new_page()
        
        target_url = "https://www.mubasher.info/markets/EGX/stocks/EGX30/announcements"
        print(f"Navigating to {target_url}")
        page.goto(target_url, wait_until="domcontentloaded")
        page.wait_for_timeout(5000)
        
        if "login" in page.url.lower():
            print("Redirected to login. Filling iframe...")
            login_frame = page.frame_locator("#loginIframe")
            
            user_input = login_frame.locator("input[type='email'], input[id='mat-input-2']").first
            user_input.type("harbharb186@gmail.com", delay=100)
            
            pass_input = login_frame.locator("input[type='password'], input[id='mat-input-3']").first
            pass_input.type("123456789Mm", delay=100)
            
            print("Pressing Enter...")
            pass_input.press("Enter")
            
            page.wait_for_timeout(5000)
            
            print("Checking for error messages...")
            # Look for error messages in the iframe
            error_msgs = login_frame.locator("text='خطأ', text='Error', .alert-danger, .error-message, [class*='error']").all_inner_texts()
            if error_msgs:
                print(f"ERRORS DETECTED: {error_msgs}")
            else:
                print("No errors detected.")
            
            print(f"URL after waiting: {page.url}")
            page.screenshot(path="data/enter_test_shot.png")
            
        browser.close()

if __name__ == "__main__":
    test_enter_login()
