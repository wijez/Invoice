from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.edge.service import Service as EdgeService
from selenium.webdriver.edge.options import Options
from selenium.webdriver.common.by import By
import time
from utils import setup, shutdown, logger


input_xpath = '//*[@id="txtCode"]'
search_xpath = '//*[@id="btnSearchInvoice"]'
close_btn_xpath = '//*[@id="showPopupInvoicNotExist"]/div[4]/button'
download_xpath = '//*[@id="popup-content-container"]/div[1]/div[2]/div[12]/div' 
menu_xpath = '//*[@id="pnResult"]/div[1]/div[1]/div[2]'
download_pdf_xpath = '//*[@id="popup-content-container"]/div[1]/div[2]/div[12]/div/div/div[1]'
download_xml_xpath = '//*[@id="popup-content-container"]/div[1]/div[2]/div[12]/div/div/div[2]'
x_btn_xpath = '//*[@id="pnResult"]/div[1]/div[2]/div[2]'


def download(driver, key):
    try:
        input_elem = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, input_xpath))
        )
        input_elem.clear()
        input_elem.send_keys(key)
        driver.find_element(By.XPATH, search_xpath).click()
        time.sleep(2)
        
        WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.XPATH, close_btn_xpath))
        )
        close_btns = driver.find_elements(By.XPATH, close_btn_xpath)
        if close_btns and close_btns[0].is_displayed() and close_btns[0].is_enabled():
            close_btns[0].click()
            logger.info("Invoice not found, closing popup.")

        
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, download_xpath))
        )
        download_btns = driver.find_elements(By.XPATH, download_xpath)
        if download_btns and download_btns[0].is_displayed() and download_btns[0].is_enabled():
            driver.execute_script("arguments[0].scrollIntoView();", download_btns[0])
            download_btns[0].click()
            time.sleep(3)
            pdf_btns = driver.find_elements(By.XPATH, download_pdf_xpath)
            if pdf_btns:
                pdf_btns[0].click()
                time.sleep(5)
                logger.info("Đã tải PDF cho mã %s.", key)
            else:
                logger.info("Không tìm thấy nút tải PDF cho mã %s.", key)
        
        else: 
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
                else:
                    logger.info("Không tìm thấy nút download cho mã %s sau khi mở menu.", key)
            else:
                logger.info("Không tìm thấy menu để mở cho mã %s.", key)
        x_btns = driver.find_elements(By.XPATH, x_btn_xpath)
        if x_btns:
            x_btns[0].click()
        logger.info("Đã xử lý mã %s.", key)
    except Exception as e:
        logger.error("Lỗi khi xử lý mã %s: e", key)
        return 
    

def process_invoice(key, webpath):
    driver = setup(webpath)
    try:
        download(driver, key)
        time.sleep(3)
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
            download(driver, key)
            time.sleep(2) 
    finally:
        shutdown(driver)