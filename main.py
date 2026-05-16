# ============================================================
#  main.py — نقطة الدخول الرئيسية
#  الاستخدام: python main.py
# ============================================================

import time
import logging
import sys
from pathlib import Path

import config
from scraper.egx_scraper import EGXScraper


# ============================================================
#  إعداد اللوق
# ============================================================

def _setup_logging():
    """يضبط اللوق: الـ console والـ file في نفس الوقت."""
    cfg = config.LOGGING
    formatter = logging.Formatter(cfg["format"])

    # Handler للـ console
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)

    # Handler للـ file
    file_handler = logging.FileHandler(cfg["log_file"], encoding=cfg["encoding"])
    file_handler.setFormatter(formatter)

    logging.basicConfig(
        level=getattr(logging, cfg["level"]),
        handlers=[console_handler, file_handler]
    )


# ============================================================
#  الدالة الرئيسية
# ============================================================

def main():
    """يشغّل الـ scraper في حلقة مستمرة."""
    _setup_logging()
    log = logging.getLogger("Main")

    # التحقق من وجود بيانات الدخول
    if not config.MUBASHER_USERNAME or not config.MUBASHER_PASSWORD:
        log.error(
            "Credentials not found. "
            "Copy .env.example to .env and fill in MUBASHER_USERNAME and MUBASHER_PASSWORD."
        )
        sys.exit(1)

    interval = config.SCRAPER["cycle_interval"]
    log.info("=" * 55)
    log.info("  EGX-Agent — Mubasher Disclosure Radar")
    log.info(f"  Cycle interval: {interval}s | DB: {config.DB_PATH}")
    log.info("=" * 55)

    while True:
        log.info("Starting new scraping cycle...")
        try:
            scraper = EGXScraper()
            scraper.run()
            log.info(f"Cycle complete. PDFs downloaded this run: {scraper.downloaded_count}")
        except Exception as e:
            log.exception(f"Unhandled error during cycle: {e}")

        log.info(f"Sleeping {interval}s until next cycle...")
        time.sleep(interval)


if __name__ == "__main__":
    main()