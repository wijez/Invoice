import logging
import time
import os
import glob
import time
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
    # options.use_chromium = True  
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-popup-blocking")
    options.add_argument("--log-level=3")
    options.add_argument("--start-maximized")
    options.add_argument("--safebrowsing-disable-download-protection")

    # Thiết lập thư mục tải về và chính sách bảo mật
    download_dir = DOWNLOAD_DIR
    os.makedirs(download_dir, exist_ok=True)

    prefs = {
        "download.default_directory": download_dir,
        "download.prompt_for_download": False,
        "download.directory_upgrade": True,
        "safebrowsing.enabled": True,
        "safebrowsing.disable_download_protection": True,
        "profile.default_content_settings.popups": 0  
    }

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


def wait_and_rename_downloaded_file(key, tax_code, ext=".xml", timeout=30):
    """
    Chờ file tải xong trong DOWNLOAD_DIR, sau đó đổi tên file mới nhất thành {key}_{tax_code}.xml
    """
    end_time = time.time() + timeout
    from . import DOWNLOAD_DIR, logger  # Đảm bảo import đúng nếu dùng package
    xml_file = None
    while time.time() < end_time:
        cr_files = glob.glob(os.path.join(DOWNLOAD_DIR, "*.crdownload"))
        if not cr_files:
            xml_files = glob.glob(os.path.join(DOWNLOAD_DIR, f"*{ext}"))
            if xml_files:
                xml_file = max(xml_files, key=os.path.getctime)
            break
        time.sleep(1)
    if xml_file:
        new_name = os.path.join(DOWNLOAD_DIR, f"{key}_{tax_code}{ext}")
        try:
            os.rename(xml_file, new_name)
            logger.info("Đã đổi tên file thành %s", new_name)
        except Exception as e:
            logger.error("Không thể đổi tên file: %s", e)
    else:
        logger.warning("Không tìm thấy file XML để đổi tên cho mã %s với MST %s.", key, tax_code)