# ============================================================
#  run_overnight.py — مُشغِّل الليل
#  الاستخدام: python run_overnight.py
#  يشغّل main.py كـ subprocess منفصل مع لوق مستقل
# ============================================================

import time
import subprocess
import logging
import sys

import config


def _setup_logging():
    """يضبط لوق مخصص للـ overnight runner."""
    formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")

    file_handler    = logging.FileHandler(
        config.LOG_DIR / "overnight.log", encoding="utf-8"
    )
    console_handler = logging.StreamHandler(sys.stdout)

    for h in [file_handler, console_handler]:
        h.setFormatter(formatter)

    logging.basicConfig(level=logging.INFO, handlers=[file_handler, console_handler])


def run_cycle():
    """يشغّل main.py كـ subprocess واحد وينتظر انتهاءه."""
    log = logging.getLogger("OvernightRunner")
    log.info("Starting scraping cycle...")

    try:
        result = subprocess.run(
            [sys.executable, "main.py"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace"
        )
        if result.stdout:
            log.info(f"STDOUT:\n{result.stdout.strip()}")
        if result.stderr:
            log.error(f"STDERR:\n{result.stderr.strip()}")
        log.info(f"Cycle finished with exit code: {result.returncode}")

    except Exception as e:
        log.error(f"Failed to run cycle: {e}")


def main():
    """الحلقة اللانهائية للـ overnight runner."""
    _setup_logging()
    log = logging.getLogger("OvernightRunner")

    interval = config.SCRAPER["cycle_interval"]
    log.info(f"EGX-Agent Overnight Runner started. Cycle interval: {interval}s")

    while True:
        run_cycle()
        log.info(f"Sleeping {interval}s until next cycle...")
        time.sleep(interval)


if __name__ == "__main__":
    main()
