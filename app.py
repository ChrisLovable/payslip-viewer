from flask import Flask, render_template, request, send_file, jsonify
from werkzeug.utils import secure_filename
import os
import PyPDF2
import io
import re
import json

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB max
app.config['SECRET_KEY'] = 'payslip-viewer-secret-key-2024'
# Simple admin secret - change this to something secure
ADMIN_SECRET = os.environ.get('ADMIN_SECRET', 'admin123')

# Ensure upload folder exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Store PDF data by month: month_key -> {pdf_path, pdf_data}
# month_key format: "YYYY-MM" (e.g., "2024-01")
monthly_pdfs = {}  # {month_key: {'path': str, 'data': {id_number: page_num}}}
DATA_FILE = 'monthly_pdfs_data.json'

def load_persisted_data():
    """Load persisted PDF data from file"""
    global monthly_pdfs
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, 'r') as f:
                data = json.load(f)
                # Verify files still exist before loading
                for month, month_data in data.items():
                    if os.path.exists(month_data['path']):
                        monthly_pdfs[month] = month_data
                    else:
                        print(f"Warning: PDF file not found for {month}: {month_data['path']}")
                print(f"Loaded {len(monthly_pdfs)} months from persistent storage")
        except Exception as e:
            print(f"Error loading persisted data: {e}")

def save_persisted_data():
    """Save PDF data to file for persistence"""
    try:
        with open(DATA_FILE, 'w') as f:
            json.dump(monthly_pdfs, f)
        print(f"Saved {len(monthly_pdfs)} months to persistent storage")
    except Exception as e:
        print(f"Error saving persisted data: {e}")

# Load persisted data on startup
load_persisted_data()

def extract_id_from_text(text):
    """Extract ID number from text - looks for common ID patterns"""
    # South African ID: 13 digits
    # Look for patterns like "ID:", "ID Number:", "Identity:", etc.
    patterns = [
        r'ID[:\s]*(\d{13})',  # ID: 1234567890123
        r'ID\s*Number[:\s]*(\d{13})',  # ID Number: 1234567890123
        r'Identity[:\s]*(\d{13})',  # Identity: 1234567890123
        r'(\d{13})',  # Just 13 digits (most common)
        r'ID[:\s]*(\d{9,13})',  # Flexible length 9-13 digits
    ]
    
    for pattern in patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        if matches:
            # Return the longest match (most likely to be the ID)
            return max(matches, key=len)
    return None

def process_pdf(pdf_path):
    """Process PDF and extract ID numbers from each page"""
    pdf_data = {}
    
    try:
        with open(pdf_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            total_pages = len(pdf_reader.pages)
            
            for page_num in range(total_pages):
                page = pdf_reader.pages[page_num]
                text = page.extract_text()
                id_number = extract_id_from_text(text)
                
                if id_number:
                    pdf_data[id_number] = page_num
                    print(f"Page {page_num + 1}: Found ID {id_number}")
                else:
                    print(f"Page {page_num + 1}: No ID found")
            
            print(f"Processed {total_pages} pages, found {len(pdf_data)} payslips with IDs")
    except Exception as e:
        print(f"Error processing PDF: {e}")
        raise
    
    return pdf_data

@app.route('/')
def index():
    # Check if admin mode (simple query parameter check)
    # Employees use regular link, admin adds ?admin=1
    is_admin = request.args.get('admin') == '1'
    return render_template('index.html', is_admin=is_admin)

@app.route('/upload', methods=['POST'])
def upload_file():
    global monthly_pdfs
    
    # Check for admin secret key in request
    admin_key = request.form.get('admin_key', '') or request.headers.get('X-Admin-Key', '')
    if admin_key != ADMIN_SECRET:
        return jsonify({'error': 'Unauthorized. Admin access required.'}), 403
    
    if 'pdf' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400
    
    month = request.form.get('month', '').strip()
    if not month:
        return jsonify({'error': 'Month selection required'}), 400
    
    # Validate month format (YYYY-MM)
    if not re.match(r'^\d{4}-\d{2}$', month):
        return jsonify({'error': 'Invalid month format. Use YYYY-MM (e.g., 2024-01)'}), 400
    
    file = request.files['pdf']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    if file and file.filename.endswith('.pdf'):
        # Save with month in filename for easier management
        filename = f"{month}_{secure_filename(file.filename)}"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        try:
            # Process PDF
            pdf_data = process_pdf(filepath)
            
            if len(pdf_data) == 0:
                # Clean up file if processing failed
                if os.path.exists(filepath):
                    os.remove(filepath)
                return jsonify({
                    'error': 'No ID numbers found in PDF. Please check the PDF format.'
                }), 400
            
            # Store by month
            monthly_pdfs[month] = {
                'path': filepath,
                'data': pdf_data
            }
            
            # Save to persistent storage
            save_persisted_data()
            
            return jsonify({
                'success': True,
                'message': f'PDF uploaded successfully for {month}! Found {len(pdf_data)} payslips.',
                'count': len(pdf_data),
                'month': month
            })
        except Exception as e:
            # Clean up file if processing failed
            if os.path.exists(filepath):
                os.remove(filepath)
            return jsonify({'error': f'Error processing PDF: {str(e)}'}), 500
    
    return jsonify({'error': 'Invalid file type. Please upload a PDF file.'}), 400

@app.route('/months', methods=['GET'])
def get_months():
    """Get list of available months"""
    months = sorted(monthly_pdfs.keys(), reverse=True)  # Most recent first
    return jsonify({'months': months})

@app.route('/view', methods=['POST'])
def view_payslip():
    global monthly_pdfs
    
    data = request.get_json()
    id_number = data.get('id_number', '').strip()
    month = data.get('month', '').strip()
    
    if not id_number:
        return jsonify({'error': 'ID number required'}), 400
    
    if not month:
        return jsonify({'error': 'Month selection required'}), 400
    
    # Validate month format
    if not re.match(r'^\d{4}-\d{2}$', month):
        return jsonify({'error': 'Invalid month format'}), 400
    
    # Check if month exists
    if month not in monthly_pdfs:
        available_months = ', '.join(sorted(monthly_pdfs.keys())) if monthly_pdfs else 'none'
        return jsonify({
            'error': f'No payslips found for {month}. Available months: {available_months}. The service may have restarted - please re-upload the PDF.'
        }), 404
    
    month_data = monthly_pdfs[month]
    pdf_path = month_data['path']
    pdf_data = month_data['data']
    
    if not os.path.exists(pdf_path):
        return jsonify({'error': 'PDF file not found. Please re-upload.'}), 404
    
    # Remove any spaces or dashes from ID number
    id_number = re.sub(r'[\s-]', '', id_number)
    
    # Find matching page
    if id_number not in pdf_data:
        return jsonify({'error': 'ID number not found. Please check your ID number and try again.'}), 404
    
    page_num = pdf_data[id_number]
    
    try:
        # Extract and return the specific page as PDF
        with open(pdf_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            pdf_writer = PyPDF2.PdfWriter()
            pdf_writer.add_page(pdf_reader.pages[page_num])
            
            # Create in-memory PDF
            output = io.BytesIO()
            pdf_writer.write(output)
            output.seek(0)
            
            # Format month name for filename
            month_name = month.replace('-', '_')
            return send_file(
                output,
                mimetype='application/pdf',
                as_attachment=False,
                download_name=f'payslip_{id_number}_{month_name}.pdf'
            )
    except Exception as e:
        return jsonify({'error': f'Error generating payslip: {str(e)}'}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)

