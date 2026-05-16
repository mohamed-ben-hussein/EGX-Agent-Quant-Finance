# ============================================================
#  scraper/browser_manager.py
#  مسؤول عن: تشغيل Brave وإنشاء جلسة Playwright عبر CDP
# ============================================================

import os
import time
import subprocess
from pathlib import Path
from playwright.sync_api import sync_playwright, BrowserContext

import config


class BrowserManager:
    """
    يدير دورة حياة متصفح Brave الكاملة:
    التشغيل ← الاتصال عبر CDP ← حقن الكوكيز ← الإيقاف
    """

    # المسارات المحتملة لملف Brave على Windows
    _BRAVE_PATHS = [
        r"C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe",
        r"C:\Program Files (x86)\BraveSoftware\Brave-Browser\Application\brave.exe",
        os.path.expanduser(r"~\AppData\Local\BraveSoftware\Brave-Browser\Application\brave.exe"),
    ]

    def __init__(self):
        self.port       = config.SCRAPER["debugging_port"]
        self.session_dir = config.BRAVE_SESSION_DIR
        self.proc       = None
        self.playwright = None
        self.browser    = None
        self.context    = None

    # ----------------------------------------------------------
    def _find_brave(self) -> str:
        """يبحث عن ملف brave.exe في المسارات الشائعة."""
        for path in self._BRAVE_PATHS:
            if os.path.exists(path):
                return path
        raise FileNotFoundError(
            "Brave browser not found. Install it or update _BRAVE_PATHS in browser_manager.py"
        )

    # ----------------------------------------------------------
    def start(self) -> BrowserContext:
        """
        يشغّل Brave مع remote debugging، يتصل به عبر Playwright CDP،
        ويحقن كوكيز البلد لتجاوز شاشة الاختيار.

        Returns:
            BrowserContext: سياق المتصفح الجاهز للاستخدام
        """
        brave_path = self._find_brave()

        self.proc = subprocess.Popen([
            brave_path,
            f"--remote-debugging-port={self.port}",
            f"--user-data-dir={self.session_dir}",
            "--no-first-run",
            "--disable-blink-features=AutomationControlled",
            "--disable-infobars",
            "--password-store=basic",
            "--no-sandbox",
        ])

        # انتظر حتى يكتمل تشغيل المتصفح
        time.sleep(5)

        self.playwright = sync_playwright().start()
        self.browser    = self.playwright.chromium.connect_over_cdp(
            f"http://localhost:{self.port}"
        )
        self.context = self.browser.contexts[0]

        # حقن كوكيز البلد لتجاوز صفحة اختيار الدولة
        expires = int(time.time()) + 86_400  # 24 ساعة
        self.context.add_cookies([
            {"name": "selected_country", "value": "eg",
             "domain": ".mubasher.info",    "path": "/", "expires": expires},
            {"name": "selected_country", "value": "eg",
             "domain": "www.mubasher.info", "path": "/", "expires": expires},
        ])

        return self.context

    # ----------------------------------------------------------
    def stop(self):
        """يغلق المتصفح والـ Playwright بأمان."""
        for obj, method in [
            (self.browser,    "close"),
            (self.playwright, "stop"),
            (self.proc,       "terminate"),
        ]:
            try:
                if obj:
                    getattr(obj, method)()
            except Exception:
                pass