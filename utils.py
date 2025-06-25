import logging
import time
import os
import glob
from selenium import webdriver 
from selenium.webdriver.edge.options import Options
from selenium.webdriver.edge.service import Service

DOWNLOAD_DIR = r"D:\RPA_RS\misa\downloads"

logging.basicConfig(
    filename='app.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def setup(webpath):
    options = Options()
    options.use_chromium = True  
    options.add_argument('--disable-web-security') 
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-popup-blocking")
    # options.add_argument("--log-level=3")
    options.add_argument("--start-maximized")
    options.add_argument("--safebrowsing-disable-download-protection")

    os.makedirs(DOWNLOAD_DIR, exist_ok=True)

    prefs = {
        "download.default_directory": DOWNLOAD_DIR,
        "download.prompt_for_download": False,
        "download.directory_upgrade": True,
        "safebrowsing.enabled": True,
        "safebrowsing.disable_download_protection": True,
        "profile.default_content_settings.popups": 0, 
        "plugins.always_open_pdf_externally": True,
    }
    logger.info("Download prefs: %s", prefs)
    options.add_experimental_option("prefs", prefs)

    service = Service()
    driver = webdriver.Edge(service=service, options=options)
    driver.get(webpath)
    return driver

def shutdown(driver):
    try:
        driver.quit()
    except Exception as e:
        logger.error("Error shutting down the driver: %s", e)

def wait_and_rename_downloaded_file(key, tax_code, ext=".pdf", timeout=30):
    end_time = time.time() + timeout
    file_path = None
    while time.time() < end_time:
        files = glob.glob(os.path.join(DOWNLOAD_DIR, f"*{ext}"))
        if files:
            file_path = max(files, key=os.path.getctime)
            break
        time.sleep(1)
    if file_path:
        new_name = os.path.join(DOWNLOAD_DIR, f"{key}_{tax_code}{ext}")
        try:
            os.rename(file_path, new_name)
            logger.info("Đã đổi tên file thành: %s", new_name)
        except Exception as e:
            logger.error("Không thể đổi tên file: %s", e)
    else:
        logger.warning("Không tìm thấy file để đổi tên sau khi tải: %s", ext)
