import pandas as pd
import os
import logging
from datetime import datetime

# Thiết lập đường dẫn file
DATA_FILE = 'demo_cms_web/Data/data.json'
SETTINGS_FILE = 'demo_cms_web/Data/settings.json'
DATA_PRO_FILE = 'demo_cms_web/Data_pro/data_pro.json'
DATA_INF_FILE = 'demo_cms_web/Data_inf/data_inf.json'
DATA_PAYMENT_FOLDER = 'demo_cms_web/Data_payment'

# Tạo thư mục nếu chưa có
os.makedirs(DATA_PAYMENT_FOLDER, exist_ok=True)

# Thiết lập logging
logging.basicConfig(level=logging.INFO)

# Load dữ liệu từ các file
reconciliation_data = pd.read_json(DATA_FILE)
product_data = pd.read_json(DATA_PRO_FILE)
influencer_data = pd.read_json(DATA_INF_FILE)
settings_data = pd.read_json(SETTINGS_FILE)

# Log kích thước của các DataFrame
logging.info(f"Reconciliation Data Shape: {reconciliation_data.shape}")
logging.info(f"Product Data Shape: {product_data.shape}")
logging.info(f"Influencer Data Shape: {influencer_data.shape}")
logging.info(f"Settings Data Shape: {settings_data.shape}")

# Kiểm tra nếu reconciliation_data rỗng
if reconciliation_data.empty:
    logging.error('No reconciliation data found.')
    exit(1)

# Tạo danh sách các creator_username từ reconciliation_data
valid_usernames = reconciliation_data['Creator username'].unique()

# Lọc influencer_data để chỉ bao gồm các creator_username hợp lệ
influencer_data_filtered = influencer_data[influencer_data['Creator username'].isin(valid_usernames)]
print(influencer_data_filtered)

# Trích xuất phí mạng
network_fee = settings_data[settings_data['variable'] == 'Network Fee']['value'].values[0] / 100
print(network_fee)
payment_entries = []

# Duyệt qua dữ liệu reconciliation
for index, row in reconciliation_data.iterrows():
    product_id = row.get('Product ID')
    est_commission_base = row.get('Est.commission base ($)')
    creator_username = row.get('Creator username')
    logging.info(f"Looking for Creator username: {creator_username}")

    # Bỏ qua hàng có giá trị NaN hoặc <= 0
    if pd.isna(est_commission_base) or est_commission_base <= 0:
        logging.warning(f"Skipping row due to invalid estimated commission base for {creator_username}: {est_commission_base}")
        continue

    # Kiểm tra sự tồn tại của product ID
    product_row = product_data[product_data['Product ID'] == product_id]
    if product_row.empty:
        logging.warning(f"Product ID {product_id} not found in product data.")
        continue
    
    bonus = 0
    affiliate_commission_rate = product_row['Affiliate Commission Rate (%)'].values[0] / 100
    approved_cms = est_commission_base * affiliate_commission_rate * (1 - network_fee)
    actual_cms = approved_cms + bonus

    # Lấy hàng influencer tương ứng
    influencer_row = influencer_data_filtered[influencer_data_filtered['Creator username'] == creator_username]
    #print(influencer_row)
    if not influencer_row.empty:
        gmail = influencer_row['Gmail'].values[0]
        bank_account = influencer_row['Payment Account'].values[0]

        payment_entry = {
            'Creator Username': creator_username,
            'Status': 'Reconciling',
            'Actual CMS': actual_cms,
            'Gmail': gmail,
            'Bank Account': bank_account,
            'Bonus': 0,
            'Approved CMS': approved_cms,
            'Occurrence Month': datetime.now().strftime('%Y-%m'),
            'Payment Date': '',  
            'Transaction ID': '', 
            'Invoice Number': ''
        }
        payment_entries.append(payment_entry)

logging.info(f"Number of payment entries created: {len(payment_entries)}")

# Lưu vào JSON nếu có payment entries
if payment_entries:
    payment_df = pd.DataFrame(payment_entries)
    grouped_payments = payment_df.groupby('Creator Username').agg({
        'Status': 'first',
        'Actual CMS': 'sum',
        'Gmail': 'first',
        'Bank Account': 'first',
        'Bonus': 'first',
        'Approved CMS': 'sum',
        'Occurrence Month': 'first',
        'Payment Date': 'first',
        'Transaction ID': 'first',
        'Invoice Number': 'first'
    }).reset_index()

    payment_file_path = os.path.join(DATA_PAYMENT_FOLDER, 'payments.json')
    grouped_payments.to_json(payment_file_path, orient='records', lines=False)
    logging.info(f"Payments saved to {payment_file_path}")
else:
    logging.info("No payment entries to save.")