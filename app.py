import json
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import pandas as pd
import os
import logging
from datetime import datetime

app = Flask(__name__)
CORS(app)

UPLOAD_FOLDER = 'uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)
    
UPLOAD_PRO_FOLDER = 'upload_product'
if not os.path.exists(UPLOAD_PRO_FOLDER):
    os.makedirs(UPLOAD_PRO_FOLDER)
    
UPLOAD_INF_FOLDER = 'upload_influencer'
if not os.path.exists(UPLOAD_INF_FOLDER):
    os.makedirs(UPLOAD_INF_FOLDER)
    
UPLOAD_PROMO_FOLDER = 'upload_promotion'
if not os.path.exists(UPLOAD_PROMO_FOLDER):
    os.makedirs(UPLOAD_PROMO_FOLDER)

DATA_FOLDER = 'Data'
if not os.path.exists(DATA_FOLDER):
    os.makedirs(DATA_FOLDER)

DATA_PRO_FOLDER = 'Data_pro'
if not os.path.exists(DATA_PRO_FOLDER):
    os.makedirs(DATA_PRO_FOLDER)
    
DATA_INF_FOLDER = 'Data_inf'
if not os.path.exists(DATA_INF_FOLDER):
    os.makedirs(DATA_INF_FOLDER)
    
DATA_PROMO_FOLDER = 'Data_promo'
if not os.path.exists(DATA_PROMO_FOLDER):
    os.makedirs(DATA_PROMO_FOLDER)
    
DATA_PAYMENT_FOLDER = 'Data_payment'
if not os.path.exists(DATA_PAYMENT_FOLDER):
    os.makedirs(DATA_PAYMENT_FOLDER)

DATA_FILE = os.path.join(DATA_FOLDER, 'data.json')
SETTINGS_FILE = os.path.join(DATA_FOLDER, 'settings.json')
DATA_PRO_FILE = os.path.join(DATA_PRO_FOLDER, 'data_pro.json')
DATA_INF_FILE = os.path.join(DATA_INF_FOLDER, 'data_inf.json')
DATA_PROMO_FILE = os.path.join(DATA_PROMO_FOLDER, 'data_promo.json')
DATA_PAYMENT_FILE = os.path.join(DATA_PAYMENT_FOLDER, 'payments.json')

# Initialize settings file if it doesn't exist
if not os.path.exists(SETTINGS_FILE):
    default_settings = [
        {
            "variable": "Affiliate Commission Rate",
            "value": 15,
            "effectiveDate": "2025-03-04"
        },
        {
            "variable": "Network Fee",
            "value": 5,
            "effectiveDate": "2025-03-04"
        }
    ]
    with open(SETTINGS_FILE, 'w') as f:
        json.dump(default_settings, f)

@app.route('/')
def index():
    return send_from_directory('pages', 'login.html')

@app.route('/demo_cms_web/pages/<path:filename>')
def serve_html(filename):
    return send_from_directory('pages', filename)

@app.route('/demo_cms_web/CSS/<path:filename>')
def serve_css(filename):
    return send_from_directory('CSS', 'style.css')

@app.route('/demo_cms_web/CSS/images/<path:filename>')
def serve_images(filename):
    return send_from_directory('CSS/images', filename)

@app.route('/demo_cms_web/uploads/<path:filename>')
def serve_uploads(filename):
    return send_from_directory('uploads', filename)

@app.route('/demo_cms_web/uploads', methods=['POST'])
def upload_file():
    # Check if the file part is present in the request
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400

    file = request.files['file']
    
    # Check if a file was selected
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    # Define the path to save the uploaded file
    file_path = os.path.join(UPLOAD_FOLDER, file.filename)
    
    try:
        # Save the uploaded file
        file.save(file_path)

        # Define the necessary columns
        columns = [
            "Sub orderid", "Creator username", "Order ID", "Product Name", "SKU",
            "Product ID", "Price ", "Quantity", "Shop Name", "Shop Code",
            "Order Status", "Content Type", "Content ID", 
            "Affiliate Partner Commission Rate (%)", "Creator Commission Rate (%)",
            "Est.commission base ($)", "Est Affiliate Partner Commission ($)",
            "Est. Creator commission ($)", "Actual commision base ($)", 
            "Actual affiliate partner commission", "Actual creator commission", 
            "Quantity returned", "Quantity refunded",
            "Time created", "Time order deliveried", "Time Comission Paid",
            "Payment ID", "Payment method", "Payment Account"
        ]

        # Load the data based on the file type
        if file.filename.endswith('.csv'):
            df = pd.read_csv(file_path)
        elif file.filename.endswith(('.xls', '.xlsx')):
            df = pd.read_excel(file_path)
        else:
            return jsonify({'error': 'Unsupported file type'}), 400
        
        # Keep only the necessary columns
        df = df[columns]

        # Read existing data if it exists
        if os.path.exists(DATA_FILE):
            old_data = pd.read_json(DATA_FILE)
            # Combine new data with old data
            df = pd.concat([old_data, df], ignore_index=True)

        # Save the combined data to a JSON file
        df.to_json(DATA_FILE, orient='records', lines=False)

        return jsonify({'message': 'File uploaded and data saved!'}), 200

    except Exception as e:
        return jsonify({'error': f'Error processing file: {str(e)}'}), 500


@app.route('/demo_cms_web/Data', methods=['GET'])
def get_data():
    page = int(request.args.get('page', 1))  # Get the page number
    per_page = 10  # Number of items per page

    if os.path.exists(DATA_FILE):
        try:
            data = pd.read_json(DATA_FILE)
            data.fillna('', inplace=True)  # Replace NaN values with empty strings
            total_records = len(data)
            total_pages = (total_records + per_page - 1) // per_page

            start = (page - 1) * per_page
            end = start + per_page
            paginated_data = data.iloc[start:end].to_dict(orient='records')

            return jsonify({
                'data': paginated_data,
                'total_pages': total_pages,
                'current_page': page
            })
        except Exception as e:
            return jsonify({'error': str(e)}), 500  # Return a JSON error message
            
    return jsonify({'data': [], 'total_pages': 0, 'current_page': 1})

@app.route('/api/settings', methods=['GET', 'POST'])
def handle_settings():
    if request.method == 'GET':
        # Load settings from the file
        with open(SETTINGS_FILE, 'r') as f:
            settings = json.load(f)
        return jsonify(settings)

    if request.method == 'POST':
        # Save settings to the file
        settings = request.json
        with open(SETTINGS_FILE, 'w') as f:
            json.dump(settings, f)
        return jsonify({'message': 'Settings updated successfully!'})

@app.route('/demo_cms_web/upload_product', methods=['POST'])
def upload_pro_file():
    # Check if the file part is present in the request
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400

    file = request.files['file']
    
    # Check if a file was selected
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    # Define the path to save the uploaded file
    file_path = os.path.join(UPLOAD_PRO_FOLDER, file.filename)
    
    try:
        # Save the uploaded file
        file.save(file_path)

        # Define the necessary columns
        columns = [
            "Product ID", "Product Name", "Price",
            "Affiliate Commission Rate (%)"
        ]

        # Load the data based on the file type
        if file.filename.endswith('.csv'):
            df = pd.read_csv(file_path)
        elif file.filename.endswith(('.xls', '.xlsx')):
            df = pd.read_excel(file_path)
        else:
            return jsonify({'error': 'Unsupported file type'}), 400
        
        # Keep only the necessary columns
        df = df[columns]

        # Read existing data if it exists
        if os.path.exists(DATA_PRO_FILE):
            old_data = pd.read_json(DATA_PRO_FILE)
            # Combine new data with old data
            df = pd.concat([old_data, df], ignore_index=True)

        # Save the combined data to a JSON file
        df.to_json(DATA_PRO_FILE, orient='records', lines=False)

        return jsonify({'message': 'File uploaded and data saved!'}), 200

    except Exception as e:
        return jsonify({'error': f'Error processing file: {str(e)}'}), 500
    
@app.route('/demo_cms_web/Data_pro', methods=['GET'])
@app.route('/demo_cms_web/Data_pro/', methods=['GET'])
def get_pro_data():
    page = int(request.args.get('page', 1))  # Get the page number
    per_page = 10  # Number of items per page

    if os.path.exists(DATA_PRO_FILE):
        try:
            data = pd.read_json(DATA_PRO_FILE)
            data.fillna('', inplace=True)  # Replace NaN values with empty strings
            total_records = len(data)
            total_pages = (total_records + per_page - 1) // per_page

            start = (page - 1) * per_page
            end = start + per_page
            paginated_data = data.iloc[start:end].to_dict(orient='records')

            return jsonify({
                'data': paginated_data,
                'total_pages': total_pages,
                'current_page': page
            })
        except Exception as e:
            return jsonify({'error': str(e)}), 500  # Return a JSON error message
            
    return jsonify({'data': [], 'total_pages': 0, 'current_page': 1})

@app.route('/demo_cms_web/upload_influencer', methods=['POST'])
def upload_inf_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400

    file = request.files['file']
    
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    file_path = os.path.join(UPLOAD_INF_FOLDER, file.filename)
    
    try:
        file.save(file_path)

        columns = [
            "Creator username", "Gmail", "Payment Account",
            "Tax ID", 'Tax (%)', 'CMS This month', 'CMS Last Month'
        ]

        if file.filename.endswith('.csv'):
            df = pd.read_csv(file_path)
        elif file.filename.endswith(('.xls', '.xlsx')):
            df = pd.read_excel(file_path)
        else:
            return jsonify({'error': 'Unsupported file type'}), 400
        
        # Kiểm tra xem các cột có tồn tại không
        missing_columns = [col for col in columns if col not in df.columns]
        if missing_columns:
            return jsonify({'error': f'Missing columns: {", ".join(missing_columns)}'}), 400

        df = df[columns]

        if os.path.exists(DATA_INF_FILE):
            old_data = pd.read_json(DATA_INF_FILE)
            df = pd.concat([old_data, df], ignore_index=True)

        df.to_json(DATA_INF_FILE, orient='records', lines=False)

        return jsonify({'message': 'File uploaded and data saved!'}), 200

    except Exception as e:
        return jsonify({'error': f'Error processing file: {str(e)}'}), 500

@app.route('/demo_cms_web/Data_inf', methods=['GET'])
@app.route('/demo_cms_web/Data_inf/', methods=['GET'])
def get_inf_data():
    if os.path.exists(DATA_INF_FILE):
        try:
            data = pd.read_json(DATA_INF_FILE)
            data.fillna('', inplace=True)  # Replace NaN values with empty strings
            total_records = len(data)

            return jsonify({
                'data': data.to_dict(orient='records'),  # Return all records
                'total_records': total_records  # Include total records
            })
        except Exception as e:
            return jsonify({'error': str(e)}), 500  # Return a JSON error message
            
    return jsonify({'data': [], 'total_records': 0})

@app.route('/demo_cms_web/upload_promotion', methods=['POST'])
def upload_promo_file():
    # Check if the file part is present in the request
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400

    file = request.files['file']
    
    # Check if a file was selected
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    # Define the path to save the uploaded file
    file_path = os.path.join(UPLOAD_PROMO_FOLDER, file.filename)
    
    try:
        # Save the uploaded file
        file.save(file_path)

        # Load the data based on the file type
        if file.filename.endswith('.csv'):
            df = pd.read_csv(file_path)
        elif file.filename.endswith(('.xls', '.xlsx')):
            df = pd.read_excel(file_path)
        else:
            return jsonify({'error': 'Unsupported file type'}), 400
        
        # Define the necessary columns
        required_columns = [
            "Campaign ID", "Campaign name", "Campaign duration", "Creator name", "Affiliate GMV", "Items sold"
        ]

        # Check if all required columns are present
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            return jsonify({'error': f'Missing columns: {", ".join(missing_columns)}'}), 400
        
        # Clean the Affiliate GMV column
        df['Affiliate GMV'] = df['Affiliate GMV'].replace({r'\$': '', ',': ''}, regex=True).astype(float)

        # Group by Campaign ID and calculate the required values
        campaign_summary = df.groupby('Campaign ID').agg(
            Campaign_Name=('Campaign name', 'first'),  # Get the first campaign name
            Campaign_Duration=('Campaign duration', 'first'),  # Get the first campaign name
            Total_Influencers=('Creator name', 'nunique'),  # Count unique creators
            Total_Items_Sold=('Items sold', 'sum'),  # Sum of items sold
            Total_Affiliate_GMV=('Affiliate GMV', 'sum')  # Sum of Affiliate GMV
        ).reset_index()

        # Calculate Total Creator CMS and Total TAP CMS
        campaign_summary['Total_Creator_CMS'] = campaign_summary['Total_Affiliate_GMV'] * 0.15 * 0.95
        campaign_summary['Total_TAP_CMS'] = campaign_summary['Total_Affiliate_GMV'] * 0.07 * 0.95
        
        # Replace NaN values with 0 for the calculated columns
        campaign_summary[['Total_Items_Sold', 'Total_Affiliate_GMV', 'Total_Creator_CMS', 'Total_TAP_CMS']] = campaign_summary[['Total_Items_Sold', 'Total_Affiliate_GMV', 'Total_Creator_CMS', 'Total_TAP_CMS']].fillna(0)
        
        # Save the summary to a JSON file or process it further as needed
        summary_file_path = os.path.join(DATA_PROMO_FOLDER, 'data_promo.json')
        campaign_summary.to_json(summary_file_path, orient='records', lines=False)

        return jsonify({'message': 'File uploaded and campaign summary generated!'}), 200

    except Exception as e:
        return jsonify({'error': f'Error processing file: {str(e)}'}), 500

@app.route('/demo_cms_web/Data_promo', methods=['GET'])
@app.route('/demo_cms_web/Data_promo/', methods=['GET'])
def get_promo_data():
    if os.path.exists(DATA_PROMO_FILE):
        try:
            data = pd.read_json(DATA_PROMO_FILE)
            data.fillna('', inplace=True)  # Replace NaN values with empty strings
            total_records = len(data)

            return jsonify({
                'data': data.to_dict(orient='records'),  # Return all records
                'total_records': total_records  # Include total records
            })
        except Exception as e:
            return jsonify({'error': str(e)}), 500  # Return a JSON error message
            
    return jsonify({'data': [], 'total_records': 0})   

@app.route('/demo_cms_web/revenue_chart/', methods=['GET'])
@app.route('/demo_cms_web/revenue_chart', methods=['GET'])
def revenue_chart():
    if not os.path.exists(DATA_PROMO_FILE):
        return jsonify({'error': 'Data file not found'}), 404

    # Load promotion data
    try:
        df = pd.read_json(DATA_PROMO_FILE)
        
        # Split Campaign Duration into Start and End Dates
        split_dates = df['Campaign_Duration'].str.split('-', expand=True)
        df['Start date'] = pd.to_datetime(split_dates[0])
        df['End date'] = pd.to_datetime(split_dates[3])
        
        # Group by month and calculate total Affiliate GMV
        df['Month'] = df['Start date'].dt.to_period('M')
        monthly_gmv = df.groupby('Month')['Total_Affiliate_GMV'].sum().reset_index()
        monthly_gmv['Month'] = monthly_gmv['Month'].dt.strftime('%Y-%m')

        return jsonify(monthly_gmv.to_dict(orient='records'))
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/demo_cms_web/Data_payment', methods=['POST'])
def create_payments():
    try:
        DATA_FILE = 'demo_cms_web\Data\data.json'  # Update with the correct path
        SETTINGS_FILE = 'demo_cms_web\Data\settings.json'
        DATA_PRO_FILE = 'demo_cms_web\Data_pro\data_pro.json'
        DATA_INF_FILE = 'demo_cms_web\Data_inf\data_inf.json'
        
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

        if reconciliation_data.empty:
            return jsonify({'error': 'No reconciliation data found.'}), 404

        valid_usernames = reconciliation_data['Creator username'].unique()
        influencer_data_filtered = influencer_data[influencer_data['Creator username'].isin(valid_usernames)]
        
        # Extract network fee
        network_fee = settings_data[settings_data['variable'] == 'Network Fee']['value'].values[0] / 100
        payment_entries = []

        # Iterate through reconciliation data
        for index, row in reconciliation_data.iterrows():
            product_id = row.get('Product ID')
            est_commission_base = row.get('Est.commission base ($)')
            creator_username = row.get('Creator username')

            if pd.isna(est_commission_base) or est_commission_base <= 0:
                logging.warning(f"Invalid estimated commission base for {creator_username}: {est_commission_base}")
                continue

            # Validate product ID existence
            product_row = product_data[product_data['Product ID'] == product_id]
            if product_row.empty:
                logging.warning(f"Product ID {product_id} not found in product data.")
                continue

            affiliate_commission_rate = product_row['Affiliate Commission Rate (%)'].values[0] / 100
            approved_cms = est_commission_base * affiliate_commission_rate * (1 - network_fee)

            influencer_row = influencer_data_filtered[influencer_data_filtered['Creator username'] == creator_username]
            if not influencer_row.empty:
                gmail = influencer_row['Gmail'].values[0]
                bank_account = influencer_row['Payment Account'].values[0]

                payment_entry = {
                    'Creator Username': creator_username,
                    'Status': 'Reconciling',
                    'Approved CMS': approved_cms,
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

        # Save to JSON if there are payment entries
        if payment_entries:
            payment_df = pd.DataFrame(payment_entries)
            grouped_payments = payment_df.groupby('Creator Username').agg({
                'Status': 'first',
                'Approved CMS': 'sum',
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

            return jsonify({'message': 'Payments created successfully!'}), 200
        else:
            logging.warning("No valid payment entries were created.")
            return jsonify({'message': 'No payments to process.'}), 200

    except Exception as e:
        logging.error(f"Error in create_payments: {str(e)}")
        return jsonify({'error': str(e)}), 500
    
@app.route('/demo_cms_web/Data_payment', methods=['GET'])
def get_payment_data():
    # Load payment data from the JSON file
    payment_file_path = os.path.join(DATA_PAYMENT_FOLDER, 'payments.json')
    if os.path.exists(payment_file_path):
        data = pd.read_json(payment_file_path)
        return jsonify(data.to_dict(orient='records')), 200
    else:
        return jsonify({'error': 'Payment data not found'}), 404

if __name__ == '__main__':
    app.run(debug=True)
