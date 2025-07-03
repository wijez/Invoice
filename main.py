import pandas as pd
import time
import re
import logging
import PyPDF2
import xmltodict
import os
import glob
from concurrent.futures import ProcessPoolExecutor, as_completed

from utils import setup, shutdown, logger, DOWNLOAD_DIR, wait_for_file_complete
from misa.misa_invoice import process_invoice as process_misa
from fpt.fpt_invoice import process_invoice as process_fpt
from e_hoadon.e_hoadon_invoice import process_invoice as process_ehoadon

patterns = {
    'invoice_number': r'Số\s*(?:\(No\.\))?\s*[:\.]?\s*([A-Z0-9]+)',
    'seller_name': r'Đơn vị bán hàng.*?[:_]\s*(.*?)(?:\n|Mã số thuế|$)',
    'seller_tax_code': r'Mã số thuế.*?[:_]\s*([0-9\s\-]{10,20})',
    'seller_address': r'Địa chỉ.*?[:_]\s*(.*?)(?:\n|Điện thoại|$)',
    'seller_account': r'Số tài khoản.*?[:_]\s*(.*?)(?:\n|$)',
    'buyer_name': r'(?:Họ tên người mua hàng|Đơn vị mua hàng).*?[:_]\s*(.*?)(?:\n|CCCD|$)',
    'buyer_address': r'(?:Địa chỉ mua|Địa chỉ).*?[:_]\s*(.*?)(?:\n|Số tài khoản|$)',
    'buyer_tax_code': r'(?:Mã số thuế mua|Mã số thuế).*?[:_]\s*([0-9\-]{10,14})'
}

SERVICE_MAP = {
    'meinvoice.vn': process_misa,
    'tracuuhoadon.fpt.com.vn': process_fpt,
    'van.ehoadon.vn': process_ehoadon
}

def match_service(url):
    for key in SERVICE_MAP:
        if key in url:
            return SERVICE_MAP[key]
    return None

def extract_data_from_xml(xml_path):
    field_map = {
        'invoice_number': ['SHDon', 'SoHoaDon', 'InvoiceNo', 'sohoadon'],
        'seller_name': ['Ten', 'TenNguoiBan', 'SellerName', 'tennguoiban'],
        'seller_tax_code': ['MST', 'MSTNguoiBan', 'SellerTaxCode', 'mstnguoiban'],
        'seller_address': ['DChi', 'DiaChiNguoiBan', 'SellerAddress', 'diachinguoiban'],
        'seller_account': ['STKNHang', 'SoTaiKhoanNguoiBan', 'SellerAccount', 'sotaikhoannguoiban'],
        'buyer_name': ['Ten', 'TenNguoiMua', 'BuyerName', 'tennguoimua'],
        'buyer_address': ['DChi', 'DiaChiNguoiMua', 'BuyerAddress', 'diachinguoimua'],
        'buyer_tax_code': ['MST', 'MSTNguoiMua', 'BuyerTaxCode', 'mstnguoimua'],
        'lookup_code': ['MaTraCuu', 'LookupCode', 'MatracCuu', 'matracuu']
    }

    def find_value(d, keys):
        if not isinstance(d, dict):
            return None
        for k, v in d.items():
            if k in keys and v:
                return v
            if isinstance(v, dict):
                found = find_value(v, keys)
                if found:
                    return found
            elif isinstance(v, list):
                for item in v:
                    found = find_value(item, keys)
                    if found:
                        return found
        return None

    try:
        with open(xml_path, 'r', encoding='utf-8') as f:
            doc = xmltodict.parse(f.read())

        data = {}
        for field, keys in field_map.items():
            value = find_value(doc, keys)
            data[field] = value
        return data if any(data.values()) else None
    except Exception as e:
        logger.error(f"Error processing XML {xml_path}: {e}")
        return None

def process_row(args):
    index, key, tax_code, webpath = args
    result = ''
    extracted_data = None

    try:
        before_files = glob.glob(os.path.join(DOWNLOAD_DIR, "*.xml"))

        service_func = match_service(webpath)
        if service_func:
            result = service_func(key, tax_code, webpath)
        else:
            result = "unsupported"

        # xml_path = os.path.join(DOWNLOAD_DIR, f"{key}_{tax_code}.xml")
        xml_candidates = [
            os.path.join(DOWNLOAD_DIR, f"{key}_{tax_code}.xml"),
            os.path.join(DOWNLOAD_DIR, f"{tax_code}{key}.xml")
        ]
        xml_path = next((f for f in xml_candidates if os.path.exists(f)), None)
        if os.path.exists(xml_path) and wait_for_file_complete(xml_path):
            logger.info(f"\u0110\u00e3 t\u1ea3i xong file XML: {xml_path}")
            extracted_data = extract_data_from_xml(xml_path)
            if extracted_data:
                logger.info(f"\u2705 extracted_data t\u1eeb {xml_path}: {extracted_data}")
            else:
                logger.warning(f"\u26a0\ufe0f Kh\u00f4ng c\u00f3 d\u1eef li\u1ec7u h\u1ee3p l\u1ec7 trong XML: {xml_path}")
        else:
            logger.warning(f"\u26a0\ufe0f Kh\u00f4ng t\u00ecm th\u1ea5y file XML sau khi t\u1ea3i cho {key}")

    except Exception as e:
        logger.error("Lỗi xử lý %s - %s: %s", key, webpath, e)
        result = 'failed'

    return index, result, extracted_data


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


if __name__ == "__main__":
    df, code_url_list = get_codes("input.xlsx")

    output_file = "output.xlsx"
    column_mapping = {
        'invoice_number': 'Số hóa đơn',
        'seller_name': 'Đơn vị bán hàng',
        'seller_tax_code': 'Mã số thuế bán',
        'seller_address': 'Địa chỉ bán',
        'seller_account': 'Số tài khoản bán',
        'buyer_name': 'Họ tên người mua hàng',
        'buyer_address': 'Địa chỉ mua',
        'buyer_tax_code': 'Mã số thuế mua',
        'lookup_code': 'Mã Tra Cứu'
    }

    if not os.path.exists(output_file):
        output_df = df.copy()
        for col in column_mapping.values():
            if col not in output_df.columns:
                output_df[col] = ''
        output_df.to_excel(output_file, index=False)

    with ProcessPoolExecutor() as executor:
        future_to_index = {executor.submit(process_row, args): args[0] for args in code_url_list}
        for future in as_completed(future_to_index):
            index, result, extracted_data = future.result()

            try:
                output_df = pd.read_excel(output_file)

                output_df.at[index, 'status'] = result or ''

                if result != 'failed' and extracted_data and any(extracted_data.values()):
                    for key, value in extracted_data.items():
                        vn_key = column_mapping.get(key, key)
                        if vn_key in output_df.columns:
                            output_df.at[index, vn_key] = value
                elif result == 'failed':
                    logger.warning(f"❌ Không ghi dữ liệu XML vì status là 'failed' tại dòng {index}")
                else:
                    logger.warning(f"\u26a0\ufe0f Kh\u00f4ng c\u00f3 d\u1eef li\u1ec7u XML h\u1ee3p l\u1ec7 t\u1ea1i dòng {index}")

                output_df.to_excel(output_file, index=False)
                logger.info(f"\u2705 Đã ghi dữ liệu vào output.xlsx tại dòng {index}")

            except Exception as e:
                logger.error(f"❌ Lỗi khi ghi dữ liệu dòng {index} vào Excel: {e}")
