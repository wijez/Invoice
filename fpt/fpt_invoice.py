from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from utils import setup, shutdown, logger, wait_and_rename_downloaded_file
import time

tax_code_xpath = '//input[@placeholder="MST bên bán"]'
key_xpath = '//input[@placeholder="Mã tra cứu hóa đơn"]'
search_xpath = '//button[contains(text(), "Tra cứu")]'
xml_xpath = '//button[contains(text(), "Tải XML")]'
arlert_xpath = "//div[contains(text(), 'Phải nhập số liệu hợp lệ cho các trường bắt buộc')]"
pdf_xpath = '//button[contains(text(), "Tra cứu")]'
    
def download(driver, key, tax_code):
    try:
        tax_elem = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, tax_code_xpath))
        )
        tax_elem.clear()
        tax_elem.send_keys(tax_code)
        key_elem = driver.find_element(By.XPATH, key_xpath)
        key_elem.clear()
        key_elem.send_keys(key)
        driver.find_element(By.XPATH, search_xpath).click()
        time.sleep(2)
        
        try:
            alert_elem = driver.find_element(By.LINK_TEXT, arlert_xpath)
            logger.warning("Thông tin không hợp lệ cho mã %s với MST %s.", key, tax_code)
            return "Failed"
        except:
            pass
        WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, pdf_xpath))
        ).click()
        time.sleep(5) 
        WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, xml_xpath))
        ).click()
        time.sleep(2) 
        logger.info("Đã tải XML cho mã %s với MST %s.", key, tax_code)
        return "Success"
    except Exception as e:
        logger.error("Lỗi khi tải XML cho mã %s với MST %s: e", key, tax_code)
        return "Failed"



def process_invoice(key,tax_code, webpath):
    driver = setup(webpath)
    try:
        result = download(driver, key, tax_code)
        wait_and_rename_downloaded_file(key, tax_code, ext=".crdownload")
    finally:
        shutdown(driver)

        
if __name__ == "__main__":
    webpath = "https://tracuuhoadon.fpt.com.vn/search.html"
    driver = setup(webpath)
    try:
        ma_tra_cuu_list = [
            ("r08e17y79g", "0304244470"),
            ("r46jvxmvxg", "0304244471"),
            ("rzmwy1yo4g", "0304308445"),
        ]
        for key, tax_code in ma_tra_cuu_list:
            download(driver, key, tax_code)
            time.sleep(3)
    finally:
        shutdown(driver)