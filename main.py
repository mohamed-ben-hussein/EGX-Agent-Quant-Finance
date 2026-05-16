# main.py

from scraper.egx_scraper import EGXScraper


import time

def main():
    print("=== EGX Mubasher Radar (Continuous Mode) ===")

    # ضع بيانات حسابك هنا لتجاوز حماية الموقع
    username = "harbharb186@gmail.com" 
    password = "123456789Mm"

    while True:
        print("\n[*] Starting new radar scan cycle...")
        try:
            scraper = EGXScraper(username=username, password=password)
            scraper.run()
            print(f"[+] Cycle completed. Downloaded {scraper.downloaded_count} new PDFs in this run.")
        except Exception as e:
            print(f"[!] Error during radar cycle: {e}")
        
        print("[*] Sleeping for 5 minutes before next scan...")
        time.sleep(300)

if __name__ == "__main__":
    main()