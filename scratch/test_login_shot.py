from playwright.sync_api import sync_playwright

def test_login():
    with sync_playwright() as p:
        browser = p.chromium.launch(executable_path=r'C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe', headless=True)
        page = browser.new_page()
        page.goto('https://community.mubasher.info/login?visitFromIframe=true')
        
        page.wait_for_timeout(3000)
        
        user_input = page.locator("input[type='email'], input[id='mat-input-2']").first
        user_input.type("harbharb186@gmail.com", delay=100)
        
        pass_input = page.locator("input[type='password'], input[id='mat-input-3']").first
        pass_input.type("123456789Mm", delay=100)
        
        login_btn = page.locator("button[type='submit'], .btn-submit").first
        page.wait_for_timeout(1000)
        login_btn.click(delay=200)
        
        page.wait_for_timeout(3000)
        
        page.screenshot(path="data/login_debug_shot.png")
        print("Screenshot saved to data/login_debug_shot.png")
        
        browser.close()

if __name__ == "__main__":
    test_login()
