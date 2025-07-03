from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
import time
from utils import setup, shutdown, logger, rename_latest_xml_file


input_xpath = '//*[@id="txtInvoiceCode"]'
search_xpath = '//*[@id="Button1"]'
save = '//*[@id="save"]'
iframe_id =  "frameViewInvoice"
download_id = "btnDownload"
pdf_id = "LinkDownPDF"
xml_id = "LinkDownXML"


def download(driver, key, taxcode=None):
    try:
        logger.info(f"Bắt đầu xử lý mã {key}")
        tax_elem = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, input_xpath ))
        )
        logger.info("Đã tìm thấy ô nhập mã tra cứu.")
        tax_elem.clear()
        tax_elem.send_keys(key)
        logger.info("Đã nhập mã tra cứu.")
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, search_xpath))
        ).click()
        logger.info("Đã nhấn nút tra cứu.")
        time.sleep(4)
        
        iframe = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, iframe_id))
        )
        logger.info("Đã tìm thấy iframe hóa đơn.")
        driver.switch_to.frame(iframe)
        btn_download = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.ID, download_id))
        )
        btn_download.click()
        logger.info("Đã nhấn nút tải xuống.")
        time.sleep(2) 
        pdf_btn = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.ID, pdf_id))
        )
        pdf_btn.click()
        logger.info("Đã nhấn nút tải PDF.")
        time.sleep(2) 
        btn_download.click()
        logger.info("Đã nhấn lại nút tải xuống để tải XML.")
        time.sleep(2) 
        xml_btn = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.ID, xml_id))
        )
        xml_btn.click()
        logger.info("Đã nhấn nút tải XML.")
        time.sleep(4) 
        # with open(f"{key}_iframe.html", "w", encoding="utf-8") as f:
        #     f.write(driver.page_source)
        driver.switch_to.default_content()
        
        rename_latest_xml_file(key, tax_code='')

        logger.info(f"Đã hoàn thành tải PDF và XML cho mã {key}")
        return "success"
    except Exception as e:
        logger.error(f"Lỗi khi xử lý mã {key}: {e}")
        return 'failed'
        

def process_invoice(key, taxcode, webpath):
    driver = setup(webpath)
    try:
        result = download(driver, key, taxcode)
        time.sleep(3)
        logger.info(f"Đã tải hóa đơn cho mã {key} .")
        return result
    except Exception as e:
        logger.error(f"Lỗi khi xử lý mã {key}")
    finally:
        shutdown(driver)

if __name__ == "__main__":
    webpath = "https://van.ehoadon.vn/TCHD?MTC="
    driver = setup(webpath)
    
    try:
        ma_tra_cuu_list = [
            "NII30XVQWNC",
            "MHPLO8W6EMD",
            "MIJ634K9JAD",
        ]
        for key in ma_tra_cuu_list:
            download(driver, key) 
    except Exception as e:
        logger.error(f"Error during download: {e}")
    finally:
        shutdown(driver)