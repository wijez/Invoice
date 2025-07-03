from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
import time
from utils import setup, shutdown, logger, rename_latest_xml_file


input_xpath = '//*[@id="txtCode"]'
search_xpath = '//*[@id="btnSearchInvoice"]'
close_btn_xpath = '//*[@id="showPopupInvoicNotExist"]/div[4]/button'
download_xpath = '//*[@id="popup-content-container"]/div[1]/div[2]/div[12]/div' 
menu_xpath = '//*[@id="pnResult"]/div[1]/div[1]/div[2]'
download_pdf_xpath = "//div[contains(@class, 'dm-item') and contains(@class, 'pdf') and contains(@class, 'txt-download-pdf')]"
download_xml_xpath = "//div[contains(@class, 'dm-item') and contains(@class, 'xml') and contains(@class, 'txt-download-xml')]"
x_btn_xpath = '//*[@id="pnResult"]/div[1]/div[2]/div[2]'


def download(driver, key, taxcode=None):
    try:
        logger.info(f"Bắt đầu xử lý mã {key}")
        input_elem = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, input_xpath))
        )
        logger.info("Đã tìm thấy ô nhập mã tra cứu.")
        input_elem.clear()
        input_elem.send_keys(key)
        driver.find_element(By.XPATH, search_xpath).click()
        logger.info("Đã nhấn nút tra cứu.")
        time.sleep(2)

        # Kiểm tra popup không tìm thấy hóa đơn
        try:
            WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.XPATH, close_btn_xpath))
            )
            close_btns = driver.find_elements(By.XPATH, close_btn_xpath)
            if close_btns and close_btns[0].is_displayed() and close_btns[0].is_enabled():
                close_btns[0].click()
                logger.info("Invoice not found, closing popup.")
                logger.info("Đã xử lý mã %s.", key)
                return
        except Exception:
            pass

        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, download_xpath))
        )
        logger.info("Đã tìm thấy nút tải xuống.")
        download_btns = driver.find_elements(By.XPATH, download_xpath)
        if download_btns and download_btns[0].is_displayed() and download_btns[0].is_enabled():
            driver.execute_script("arguments[0].scrollIntoView();", download_btns[0])
            download_btns[0].click()
            logger.info("Đã nhấn nút tải xuống.")
            time.sleep(3)
            pdf_btns = WebDriverWait(driver, 10).until(
                EC.presence_of_all_elements_located((By.XPATH, download_pdf_xpath))
            )
            if pdf_btns:
                pdf_btns[0].click()
                logger.info("Đã nhấn nút tải PDF.")
            else:
                logger.warning("Không tìm thấy nút tải PDF.")
            time.sleep(2)
            download_btns[0].click()
            logger.info("Đã nhấn lại nút tải xuống để tải XML.")
            time.sleep(2)
            xml_btns = WebDriverWait(driver, 10).until(
                EC.presence_of_all_elements_located((By.XPATH, download_xml_xpath))
            )
            driver.execute_script("arguments[0].scrollIntoView();", xml_btns[0])
            xml_btns[0].click()
            logger.info("Đã nhấn nút tải XML.")
            time.sleep(2)
            logger.info("Đã tải PDF và XML cho mã %s.", key)
        else:
            logger.warning("Không tìm thấy hoặc không thể nhấn nút tải xuống.")
            # Thử mở menu để tìm nút tải PDF và XML
            menu_btns = driver.find_elements(By.XPATH, menu_xpath)
            if menu_btns:
                menu_btns[0].click()
                time.sleep(2)
                download_btns = driver.find_elements(By.XPATH, download_xpath)
                if download_btns:
                    download_btns[0].click()
                    time.sleep(2)
                    pdf_btns = driver.find_elements(By.XPATH, download_pdf_xpath)
                    if pdf_btns:
                        pdf_btns[0].click()
                        time.sleep(2)
                        logger.info("Đã tải PDF cho mã %s sau khi mở menu.", key)
                    else:
                        logger.info("Không tìm thấy nút tải PDF cho mã %s sau khi mở menu.", key)
                    # Thực hiện tải XML sau khi mở menu
                    download_btns[0].click()
                    time.sleep(2)
                    xml_btns = driver.find_elements(By.XPATH, download_xml_xpath)
                    if xml_btns:
                        driver.execute_script("arguments[0].scrollIntoView();", xml_btns[0])
                        xml_btns[0].click()
                        time.sleep(2)
                        logger.info("Đã tải XML cho mã %s sau khi mở menu.", key)
                    else:
                        logger.info("Không tìm thấy nút tải XML cho mã %s sau khi mở menu.", key)
                else:
                    logger.info("Không tìm thấy nút download cho mã %s sau khi mở menu.", key)
            else:
                logger.info("Không tìm thấy menu để mở cho mã %s.", key)
        logger.info("Đã xử lý mã %s.", key)
        rename_latest_xml_file(key, tax_code='')
        # Đóng popup kết quả nếu có
        x_btns = driver.find_elements(By.XPATH, x_btn_xpath)
        if x_btns:
            x_btns[0].click()
        logger.info("Đã xử lý mã %s.", key)
        return "success"
    except Exception as e:
        logger.error("Lỗi khi xử lý mã %s: %s", key, e)
        return "failed"
    

def process_invoice(key, taxcode, webpath):
    driver = setup(webpath)
    try:
        result = download(driver, key, taxcode)
        time.sleep(3)
        return result
    finally:
        shutdown(driver)

if __name__ == "__main__":
    webpath = "https://www.meinvoice.vn/tra-cuu"
    driver = setup(webpath)
    try:
        ma_tra_cuu_list = [
            "B1HEIRR8N0WP",
            "MÃ_2",
            "MÃ_3",
            "B1HEIRR8N0WP",
        ]
        for key in ma_tra_cuu_list:
            download(driver, key, "")
            time.sleep(2) 
    finally:
        shutdown(driver)