from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from utils import setup, shutdown, logger, wait_and_rename_downloaded_file, DOWNLOAD_DIR
import time
import base64
import pyautogui
import os

tax_code_xpath = '//input[@placeholder="MST bên bán"]'
key_xpath = '//input[@placeholder="Mã tra cứu hóa đơn"]'
search_xpath = '//button[contains(text(), "Tra cứu")]'
xml_xpath = '//button[contains(text(), "Tải XML")]'
arlert_xpath = "//div[contains(text(), 'Phải nhập số liệu hợp lệ cho các trường bắt buộc')]"
pdf_xpath = '//button[.//span[contains(@class, "wxi-search")] and contains(text(), "Tra cứu")]'
save_btn_xpath = [
            '//button[@id="save"]',
            '//button[@title="Save (Ctrl+S)"]',
            '//button[contains(@class, "c0163")]',
            '//button[.//div[contains(@class, "c0168")]]',
            '//button[.//svg[@width="20" and @height="20"]]',
            '//button[@data-element-focusable="true" and .//div[contains(@class, "c0168")]]'
        ]


def get_invoice_iframe_src(driver):
    try:
        iframe = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, '//div[@view_id="search:ipdf"]//iframe'))
        )
        src = iframe.get_attribute("src")
        logger.info(f"Link hóa đơn trong iframe: {src}")
        return src, iframe
    except Exception as e:
        logger.error(f"Không lấy được link hóa đơn trong iframe: {e}")
        return None
    
    
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
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, search_xpath))
        ).click()
        time.sleep(4)
        
        invoice_src, iframe = get_invoice_iframe_src(driver)
        iframe = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, '//div[@view_id="search:ipdf"]//iframe'))
        )
        driver.switch_to.frame(iframe)
        time.sleep(5)
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
            logger.info("Đã lưu file PDF từ blob.")
        logger.info(f"Link hóa đơn PDF: {invoice_src}")
        
        # with open("iframe_debug.html", "w", encoding="utf-8") as f:
        #     f.write(driver.page_source)
        # driver.save_screenshot("iframe_save_debug.png")
        logger.info("Đã ghi file iframe_debug.html để kiểm tra blob iframe")

        driver.switch_to.default_content()
        logger.info("Đã hoàn tất xử lý cho mã %s với MST %s.", key, tax_code)

    except TimeoutException:
        logger.warning("Không tìm thấy %s với MST %s.", key, tax_code)



def process_invoice(key,tax_code, webpath):
    driver = setup(webpath)
    try:
        download(driver, key, tax_code)
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