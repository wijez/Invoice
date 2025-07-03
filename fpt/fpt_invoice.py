from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from utils import setup, shutdown, logger, DOWNLOAD_DIR, rename_latest_xml_file
import time
import base64
import os
import re

tax_code_xpath = '//input[@placeholder="MST bên bán"]'
key_xpath = '//input[@placeholder="Mã tra cứu hóa đơn"]'
search_xpath = '//button[contains(text(), "Tra cứu")]'
xml_xpath = '//button[contains(text(), "Tải XML")]'
arlert_xpath = "//div[contains(text(), 'Phải nhập số liệu hợp lệ cho các trường bắt buộc')]"
pdf_xpath = '//button[.//span[contains(@class, "wxi-search")] and contains(text(), "Tra cứu")]'
iframe_xpath = '//div[@view_id="search:ipdf"]//iframe'


def get_invoice_iframe_src(driver, iframe_xpath):
    try:
        iframe = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, iframe_xpath))
        )
        src = iframe.get_attribute("src")
        logger.info(f"Link hóa đơn trong iframe: {src}")
        return src, iframe
    except Exception as e:
        logger.error(f"Không lấy được link hóa đơn trong iframe: {e}")
        return None
    
    
def download(driver, key, tax_code):
    try:
        logger.info(f"Bắt đầu xử lý mã {key} với MST {tax_code}")
        tax_elem = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, tax_code_xpath))
        )
        logger.info("Đã tìm thấy ô nhập MST bên bán.")
        tax_elem.clear()
        tax_elem.send_keys(tax_code)
        key_elem = driver.find_element(By.XPATH, key_xpath)
        key_elem.clear()
        key_elem.send_keys(key)
        logger.info("Đã nhập mã tra cứu hóa đơn.")
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, search_xpath))
        ).click()
        logger.info("Đã nhấn nút tra cứu.")
        time.sleep(4)
        
        invoice_src, iframe = get_invoice_iframe_src(driver, iframe_xpath)
        if not invoice_src:
            logger.error(f"Không tìm thấy iframe cho mã {key}.")
            return "failed"

        logger.info("Đã tìm thấy iframe hóa đơn.")
        driver.switch_to.frame(iframe)
        time.sleep(5)
        logger.info("Đang thực hiện lấy blob PDF từ iframe.")
        js = """
        var iframeBlob = window.location.href;
        fetch(iframeBlob)
        .then(r => r.blob())
        .then(blob => {
            var reader = new FileReader();
            reader.onload = function() {
            window.blobBase64 = reader.result;
            };
            reader.readAsDataURL(blob);
        });
        """
        driver.execute_script(js)
        time.sleep(2)
        blob_base64 = driver.execute_script("return window.blobBase64;")
        if blob_base64:
            header, encoded = blob_base64.split(",", 1)
            pdf_path = os.path.join(DOWNLOAD_DIR, f"{key}_{tax_code}.pdf")
            with open(pdf_path, "wb") as f:
                f.write(base64.b64decode(encoded))
            logger.info(f"Đã lưu file PDF từ blob: {pdf_path}")
        else:
            logger.warning("Không lấy được dữ liệu blob PDF.")
        logger.info(f"Link hóa đơn PDF: {invoice_src}")
        # with open("iframe_debug.html", "w", encoding="utf-8") as f:
        #     f.write(driver.page_source)
        # driver.save_screenshot("iframe_save_debug.png")
        logger.info("Đã ghi file iframe_debug.html để kiểm tra blob iframe")

        driver.switch_to.default_content()
        logger.info("Đã chuyển về frame chính.")
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, xml_xpath))
        ).click()
        # rename_latest_xml_file(key, tax_code)
        logger.info("Đã nhấn nút tải XML.")
        time.sleep(2)
        logger.info("Đã hoàn tất xử lý cho mã %s với MST %s.", key, tax_code)
        return "success"
    
    except TimeoutException:
        logger.warning("Không tìm thấy %s với MST %s.", key, tax_code)
        return "failed"
    except Exception as e:
        logger.error(f"Lỗi khi xử lý mã {key} với MST {tax_code}: {e}")
        return "failed"


def process_invoice(key,tax_code, webpath):
    driver = setup(webpath)
    try:
        result = download(driver, key, tax_code)
        time.sleep(3)
        return result
    finally:
        shutdown(driver)



if __name__ == "__main__":
    webpath = "https://tracuuhoadon.fpt.com.vn/search.html"
    driver = setup(webpath)
    try:
        ma_tra_cuu_list = [
            ("r08e17y79g", "0304244470"),
            # ("r46jvxmvxg", "0304244471"),
            # ("rzmwy1yo4g", "0304308445"),
        ]
        for key, tax_code in ma_tra_cuu_list:
            download(driver, key, tax_code)
            time.sleep(30)
    finally:
        shutdown(driver)