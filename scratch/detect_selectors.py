from playwright.sync_api import sync_playwright
import sys

def detect():
    with sync_playwright() as p:
        browser = p.chromium.launch(executable_path=r'C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe', headless=True)
        page = browser.new_page()
        page.goto('https://community.mubasher.info/login?visitFromIframe=true')
        page.wait_for_timeout(5000)
        
        print("--- INPUTS ---")
        inputs = page.query_selector_all('input')
        for i in inputs:
            itype = i.get_attribute('type')
            iname = i.get_attribute('name')
            iid = i.get_attribute('id')
            iclass = i.get_attribute('class')
            print(f"Type: {itype} | Name: {iname} | ID: {iid} | Class: {iclass}")
            
        print("\n--- BUTTONS ---")
        buttons = page.query_selector_all('button')
        for b in buttons:
            btype = b.get_attribute('type')
            bclass = b.get_attribute('class')
            print(f"Type: {btype} | Class: {bclass}")
            
        browser.close()

if __name__ == "__main__":
    detect()
