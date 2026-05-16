import requests
import urllib3

# Suppress insecure request warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

url = "https://www.egx.com.eg/downloads/News/188059_152608.pdf"
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
    "Accept-Language": "en-US,en;q=0.9,ar;q=0.8",
    "Referer": "https://www.mubasher.info/"
}

try:
    print(f"Fetching {url}...")
    # Follow redirects is True by default
    response = requests.get(url, headers=headers, timeout=30, verify=False)
    print(f"Status: {response.status_code}")
    print(f"Content-Type: {response.headers.get('Content-Type')}")
    print(f"First 100 bytes: {response.content[:100]}")
    
    if b'%PDF' in response.content[:1024]:
        print("SUCCESS: It is a PDF!")
    else:
        print("FAILURE: Still getting HTML or other content.")
        with open(r"c:\Users\Hady\EGX-Agent\scratch\debug_download.html", "wb") as f:
            f.write(response.content)
        print(r"Saved debug content to c:\Users\Hady\EGX-Agent\scratch\debug_download.html")

except Exception as e:
    print(f"Error: {e}")
