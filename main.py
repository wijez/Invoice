import pandas as pd
import time
import logging
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.edge.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from concurrent.futures import ProcessPoolExecutor, as_completed

from utils import setup, shutdown, logger
from misa.misa_invoice import process_invoice as process_misa
from fpt.fpt_invoice import process_invoice as process_fpt
from e_hoadon.e_hoadon_invoice import process_invoice as process_ehoadon




def get_codes(filepath):
    df = pd.read_excel(filepath, dtype={'Mã số thuế': str, 'Mã tra cứu': str})
    df['status'] = ''
    code_url_list = []
    for _, row in df.iterrows():
        code_search = row['Mã tra cứu']
        tax_code = row['Mã số thuế']
        url = row['URL']
        if pd.notna(code_search) and pd.notna(url):
            code_url_list.append((_, 
                                  str(code_search).strip(),
                                  str(tax_code).strip() if pd.notna(tax_code) else "", 
                                  str(url).strip())
                                 )
    return df, code_url_list


def process_row(args):
    index, key, tax_code, webpath = args
    result = ''
    try:
        if "meinvoice.vn" in webpath:
            process_misa(key, webpath)  
            result = "Success"
        elif "tracuuhoadon.fpt.com.vn" in webpath:
            result = process_fpt(key, tax_code, webpath) 
        elif "van.ehoadon.vn" in webpath:
            process_ehoadon(key, webpath)  
            result = "Success"
        else:
            result = 'unsupported'
    except Exception as e:
        logging.error("Lỗi xử lý %s - %s: %s", key, webpath, e)
        result = 'failed'
    return (index, result)


if __name__ == "__main__":
    df, code_url_list = get_codes("input.xlsx")

    results = []

    with ProcessPoolExecutor() as executor:
        future_to_index = {executor.submit(process_row, args): args[0] for args in code_url_list}
        for future in as_completed(future_to_index):
            index, result = future.result()
            if result != "Success":
                df.at[index, 'status'] = result or ''

    df.to_excel("output.xlsx", index=False)