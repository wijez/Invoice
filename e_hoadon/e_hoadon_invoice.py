from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.edge.service import Service as EdgeService
from selenium.webdriver.common.by import By
import time
from utils import setup, shutdown, logger

input_xpath = '//*[@id="txtInvoiceCode"]'
search_xpath = '//*[@id="Button1"]'
save = '//*[@id="save"]'
iframe_id =  "frameViewInvoice"
download_id = "btnDownload"
pdf_id = "LinkDownPDF"
xml_id = "LinkDownXML"

def download(driver, key):
    try:
        tax_elem = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, input_xpath ))
        )
        tax_elem.clear()
        tax_elem.send_keys(key)
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, search_xpath))
        ).click()
        time.sleep(4)
        
        iframe = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, iframe_id))
        )
        driver.switch_to.frame(iframe)
        btn_download = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.ID, download_id))
        )
        btn_download.click()
        time.sleep(1) 
        pdf_btn = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.ID, pdf_id))
        )
        pdf_btn.click()
        time.sleep(2) 
        btn_download.click()
        # Click nút Download XML
        xml_btn = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.ID, xml_id))
        )
        xml_btn.click()
      
        time.sleep(10) 
        # with open(f"{key}_iframe.html", "w", encoding="utf-8") as f:
        #     f.write(driver.page_source)
        
        driver.switch_to.default_content()

    except Exception as e:
        logger.error(f"Lỗi khi xử lý mã {key}: {e}")
        

def process_invoice(key, webpath):
    driver = setup(webpath)
    try:
        download(driver, key)
        logger.info(f"Đã tải hóa đơn cho mã {key} .")
    except Exception as e:
        logger.error(f"Lỗi khi xử lý mã {key}")
    finally:
        shutdown(driver)

if __name__ == "__main__":
    webpath = "https://van.ehoadon.vn/TCHD?MTC="
    driver = setup(webpath)
    
    try:
        download(driver, "NII30XVQWNC") 
    except Exception as e:
        logger.error(f"Error during download: {e}")
    finally:
        shutdown(driver)