# scraper/browser_manager.py

import os
import time
import subprocess
from pathlib import Path
from playwright.sync_api import sync_playwright


class BrowserManager:
    def __init__(self, debugging_port=9222):
        self.debugging_port = debugging_port
        self.proc = None
        self.playwright = None
        self.browser = None
        self.context = None

    def _find_brave(self):
        paths = [
            r"C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe",
            r"C:\Program Files (x86)\BraveSoftware\Brave-Browser\Application\brave.exe",
            os.path.expanduser("~") + r"\AppData\Local\BraveSoftware\Brave-Browser\Application\brave.exe"
        ]

        for path in paths:
            if os.path.exists(path):
                return path

        return None

    def start(self):
        brave_path = self._find_brave()

        if not brave_path:
            raise FileNotFoundError("Brave browser not found.")

        user_data_dir = Path("c:/Users/Hady/EGX-Agent/brave_session")
        user_data_dir.mkdir(parents=True, exist_ok=True)

        self.proc = subprocess.Popen([
            brave_path,
            f"--remote-debugging-port={self.debugging_port}",
            f"--user-data-dir={user_data_dir}",
            "--no-first-run",
            "--disable-blink-features=AutomationControlled",
            "--disable-infobars",
            "--password-store=basic",
            "--no-sandbox"
        ])

        time.sleep(5)

        self.playwright = sync_playwright().start()

        self.browser = self.playwright.chromium.connect_over_cdp(
            f"http://localhost:{self.debugging_port}"
        )

        self.context = self.browser.contexts[0]

        # Inject cookies to bypass country selection
        expires = time.time() + 3600 * 24 # 24 hours
        cookies = [
            {"name": "selected_country", "value": "eg", "domain": ".mubasher.info", "path": "/", "expires": expires},
            {"name": "selected_country", "value": "eg", "domain": "www.mubasher.info", "path": "/", "expires": expires}
        ]
        self.context.add_cookies(cookies)

        return self.context

    def stop(self):
        try:
            if self.browser:
                self.browser.close()

            if self.playwright:
                self.playwright.stop()

            if self.proc:
                self.proc.terminate()

        except Exception:
            pass