# run_overnight.py
import time
import subprocess
import logging
import sys

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("overnight_process.log"),
        logging.StreamHandler(sys.stdout)
    ]
)

log = logging.getLogger("Overnight-Runner")

def run_scraper():
    log.info("Starting a new scraping cycle...")
    try:
        # Run main.py and wait for it to finish
        result = subprocess.run(["python", "main.py"], capture_output=True, text=True)
        log.info("Scraping cycle completed.")
        if result.stdout:
            log.info(f"STDOUT: {result.stdout}")
        if result.stderr:
            log.error(f"STDERR: {result.stderr}")
    except Exception as e:
        log.error(f"Error during scraping cycle: {e}")

if __name__ == "__main__":
    log.info("EGX-Radar Overnight Mission Started!")
    while True:
        run_scraper()
        log.info("Sleeping for 30 minutes until next cycle...")
        time.sleep(1800) # 30 minutes
