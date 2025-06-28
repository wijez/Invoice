import logging
import time
import os
import pdfplumber
import re
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



def extract_invoice_info(pdf_path):
    data = {
        "Số hóa đơn": None,
        "Đơn vị bán hàng": None,
        "MST bán": None,
        "Địa chỉ bán": None,
        "STK bán": None,
        "Họ tên người mua": None,
        "Địa chỉ mua": None,
        "MST mua": None
    }

    with pdfplumber.open(pdf_path) as pdf:
        text = ""
        for page in pdf.pages:
            text += page.extract_text() + "\n"

    # Xử lý regex từng trường
    data["Số hóa đơn"] = re.search(r"Số [\s\(]?hóa đơn[\s\)]*[:\-]?\s*(\S+)", text, re.IGNORECASE)
    data["Đơn vị bán hàng"] = re.search(r"Đơn vị bán hàng\s*[:\-]?\s*(.+)", text)
    data["MST bán"] = re.search(r"Mã số thuế\s*[:\-]?\s*(\d+)", text)
    data["Địa chỉ bán"] = re.search(r"Địa chỉ\s*[:\-]?\s*(.+)", text)
    data["STK bán"] = re.search(r"Số tài khoản\s*[:\-]?\s*(.+)", text)
    data["Họ tên người mua"] = re.search(r"Họ tên người mua hàng\s*[:\-]?\s*(.+)", text)
    data["Địa chỉ mua"] = re.search(r"Địa chỉ.*?[:\-]?\s*(.+)", text)
    data["MST mua"] = re.search(r"Mã số thuế.*?[:\-]?\s*(\d+)", text)

    # Làm sạch kết quả
    for k, v in data.items():
        data[k] = v.group(1).strip() if v else "Không tìm thấy"

    return data


def extract_pdf_fields(pdf_path):
    with pdfplumber.open(pdf_path) as pdf:
        text = "\n".join(page.extract_text() for page in pdf.pages)

    def extract(pattern, name):
        match = re.search(pattern, text)
        return match.group(1).strip() if match else f"[Không tìm thấy {name}]"

    return {
        "Số hóa đơn": extract(r"Số\s*(?:hóa đơn)?[:\-]?\s*(\w+)", "số hóa đơn"),
        "Đơn vị bán hàng": extract(r"Đơn vị bán hàng.*?:\s*(.+)", "đơn vị bán hàng"),
        "MST bán": extract(r"Mã số thuế.*?:\s*(\d+)", "mst bán"),
        "Địa chỉ bán": extract(r"Địa chỉ.*?:\s*(.+)", "địa chỉ bán"),
        "STK bán": extract(r"Số tài khoản.*?:\s*(.+)", "stk bán"),
        "Họ tên người mua": extract(r"Họ tên người mua hàng.*?:\s*(.+)", "người mua"),
        "Địa chỉ mua": extract(r"Địa chỉ.*?:\s*(.+)", "địa chỉ mua"),
        "MST mua": extract(r"Mã số thuế.*?:\s*(\d+)", "mst mua"),
    }