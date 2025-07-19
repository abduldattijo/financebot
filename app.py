"""
Flask Web Application for Nigerian Bank Statement Transformer
Optimized for M4 MacBook with PyCharm
"""

from flask import Flask, request, jsonify, render_template_string, send_file
from werkzeug.utils import secure_filename
import os
import tempfile
from pathlib import Path
import uuid
from bank_transformer import BankStatementTransformer
import logging
import pandas as pd

# Initialize Flask app
app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB max file size
app.config['UPLOAD_FOLDER'] = tempfile.mkdtemp()

# Initialize transformer
transformer = BankStatementTransformer()

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Allowed file extensions
ALLOWED_EXTENSIONS = {'xlsx', 'xls', 'ods'}


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


# HTML Template
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Nigerian Financial Intelligence Agency - Bank Statement Transformer</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { 
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; 
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        .container { 
            max-width: 1200px; 
            margin: 0 auto; 
            background: white; 
            border-radius: 15px; 
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
            overflow: hidden;
        }
        .header { 
            background: #2c3e50; 
            color: white; 
            padding: 30px; 
            text-align: center; 
        }
        .header h1 { font-size: 2.2em; margin-bottom: 10px; }
        .header p { opacity: 0.9; font-size: 1.1em; }
        .main-content { padding: 40px; }
        .upload-section { 
            border: 3px dashed #ddd; 
            border-radius: 10px; 
            padding: 40px; 
            text-align: center; 
            margin-bottom: 30px;
            transition: all 0.3s ease;
        }
        .upload-section:hover { border-color: #667eea; background: #f8f9ff; }
        .upload-section input[type="file"] { 
            width: 100%; 
            padding: 15px; 
            border: 2px solid #ddd; 
            border-radius: 8px; 
            font-size: 16px;
            margin: 15px 0;
        }
        .btn { 
            background: #667eea; 
            color: white; 
            padding: 15px 30px; 
            border: none; 
            border-radius: 8px; 
            font-size: 16px; 
            cursor: pointer; 
            transition: all 0.3s ease;
            margin: 5px;
        }
        .btn:hover { background: #5a67d8; transform: translateY(-2px); }
        .btn:disabled { background: #ccc; cursor: not-allowed; }
        .btn-small {
            padding: 8px 15px;
            font-size: 12px;
        }
        .btn-preview {
            background: #17a2b8;
        }
        .btn-preview:hover {
            background: #138496;
        }
        .btn-download {
            background: #28a745;
        }
        .btn-download:hover {
            background: #218838;
        }
        .results { 
            margin-top: 30px; 
            padding: 20px; 
            background: #f8f9fa; 
            border-radius: 10px; 
            display: none;
        }
        .success { color: #28a745; }
        .error { color: #dc3545; }
        .file-item { 
            background: white; 
            padding: 15px; 
            margin: 10px 0; 
            border-radius: 8px; 
            border-left: 4px solid #667eea;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .progress { 
            width: 100%; 
            height: 20px; 
            background: #e9ecef; 
            border-radius: 10px; 
            overflow: hidden; 
            margin: 10px 0;
            display: none;
        }
        .progress-bar { 
            height: 100%; 
            background: #28a745; 
            transition: width 0.3s ease;
        }
        .config-section {
            background: #f8f9fa;
            padding: 20px;
            border-radius: 10px;
            margin-bottom: 20px;
        }
        .config-row {
            display: flex;
            gap: 20px;
            margin-bottom: 15px;
        }
        .config-item {
            flex: 1;
        }
        .config-item label {
            display: block;
            margin-bottom: 5px;
            font-weight: 600;
            color: #2c3e50;
        }
        .config-item select, .config-item input {
            width: 100%;
            padding: 10px;
            border: 2px solid #ddd;
            border-radius: 5px;
            font-size: 14px;
        }
        .status-badge {
            padding: 5px 10px;
            border-radius: 20px;
            font-size: 12px;
            font-weight: 600;
        }
        .status-success { background: #d4edda; color: #155724; }
        .status-processing { background: #fff3cd; color: #856404; }
        .status-error { background: #f8d7da; color: #721c24; }

        /* Preview Modal Styles */
        .modal {
            display: none;
            position: fixed;
            z-index: 1000;
            left: 0;
            top: 0;
            width: 100%;
            height: 100%;
            background-color: rgba(0,0,0,0.5);
        }
        .modal-content {
            background-color: white;
            margin: 2% auto;
            padding: 0;
            border-radius: 10px;
            width: 95%;
            max-width: 1100px;
            max-height: 90vh;
            overflow: hidden;
            box-shadow: 0 20px 40px rgba(0,0,0,0.3);
        }
        .modal-header {
            background: #2c3e50;
            color: white;
            padding: 20px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .modal-header h3 {
            margin: 0;
        }
        .close {
            background: none;
            border: none;
            color: white;
            font-size: 28px;
            font-weight: bold;
            cursor: pointer;
        }
        .close:hover {
            opacity: 0.7;
        }
        .modal-body {
            padding: 20px;
            max-height: 70vh;
            overflow-y: auto;
        }
        .preview-table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 15px;
        }
        .preview-table th,
        .preview-table td {
            border: 1px solid #ddd;
            padding: 8px;
            text-align: left;
            font-size: 12px;
        }
        .preview-table th {
            background-color: #f8f9fa;
            font-weight: 600;
            position: sticky;
            top: 0;
            z-index: 10;
        }
        .preview-table tr:nth-child(even) {
            background-color: #f9f9f9;
        }
        .preview-info {
            background: #e3f2fd;
            padding: 15px;
            border-radius: 5px;
            margin-bottom: 15px;
        }
        .loading {
            text-align: center;
            padding: 40px;
        }
        .spinner {
            border: 4px solid #f3f3f3;
            border-top: 4px solid #667eea;
            border-radius: 50%;
            width: 40px;
            height: 40px;
            animation: spin 1s linear infinite;
            margin: 0 auto 20px;
        }
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🏛️ Nigerian Financial Intelligence Agency</h1>
            <p>Bank Statement Standardization System</p>
            <p>🔒 Secure • ⚡ Fast • 📊 Standardized</p>
        </div>

        <div class="main-content">
            <!-- Configuration Section -->
            <div class="config-section">
                <h3 style="margin-bottom: 15px; color: #2c3e50;">⚙️ Processing Configuration</h3>
                <div class="config-row">
                    <div class="config-item">
                        <label for="dateFormat">Date Format:</label>
                        <select id="dateFormat">
                            <option value="DD/MM/YYYY">DD/MM/YYYY (Nigerian Standard)</option>
                            <option value="MM/DD/YYYY">MM/DD/YYYY (US Format)</option>
                            <option value="YYYY-MM-DD">YYYY-MM-DD (ISO Format)</option>
                        </select>
                    </div>
                    <div class="config-item">
                        <label for="currency">Currency:</label>
                        <select id="currency">
                            <option value="NGN">Nigerian Naira (₦)</option>
                            <option value="USD">US Dollar ($)</option>
                            <option value="GBP">British Pound (£)</option>
                        </select>
                    </div>
                    <div class="config-item">
                        <label for="includeMetadata">Include Metadata:</label>
                        <input type="checkbox" id="includeMetadata" checked> Account info & summary
                    </div>
                </div>
            </div>

            <!-- Upload Section -->
            <div class="upload-section">
                <h3>📤 Upload Bank Statements</h3>
                <p>Supports XLSX, XLS, and ODS formats from Nigerian banks</p>
                <input type="file" id="fileInput" multiple accept=".xlsx,.xls,.ods">
                <div class="progress" id="progressBar">
                    <div class="progress-bar" style="width: 0%"></div>
                </div>
                <button class="btn" id="uploadBtn" onclick="processFiles()">Transform Files</button>
            </div>

            <!-- Results Section -->
            <div class="results" id="results">
                <h3>📋 Processing Results</h3>
                <div id="fileResults"></div>
            </div>
        </div>
    </div>

    <!-- Preview Modal -->
    <div id="previewModal" class="modal">
        <div class="modal-content">
            <div class="modal-header">
                <h3>📊 File Preview</h3>
                <button class="close" onclick="closePreview()">&times;</button>
            </div>
            <div class="modal-body" id="previewContent">
                <div class="loading">
                    <div class="spinner"></div>
                    <p>Loading preview...</p>
                </div>
            </div>
        </div>
    </div>

    <script>
        let uploadedFiles = [];

        document.getElementById('fileInput').addEventListener('change', function(e) {
            uploadedFiles = Array.from(e.target.files);
            updateFileDisplay();
        });

        function updateFileDisplay() {
            const resultsDiv = document.getElementById('results');
            const fileResultsDiv = document.getElementById('fileResults');

            if (uploadedFiles.length > 0) {
                resultsDiv.style.display = 'block';
                fileResultsDiv.innerHTML = `
                    <h4>📁 Selected Files (${uploadedFiles.length})</h4>
                    ${uploadedFiles.map(file => `
                        <div class="file-item">
                            <div>
                                <strong>${file.name}</strong><br>
                                <small>${(file.size / 1024 / 1024).toFixed(2)} MB</small>
                            </div>
                            <span class="status-badge status-processing">Ready</span>
                        </div>
                    `).join('')}
                `;
            }
        }

        async function processFiles() {
            if (uploadedFiles.length === 0) {
                alert('Please select files first!');
                return;
            }

            const uploadBtn = document.getElementById('uploadBtn');
            const progressBar = document.getElementById('progressBar');
            const progressBarInner = progressBar.querySelector('.progress-bar');

            uploadBtn.disabled = true;
            uploadBtn.textContent = 'Processing...';
            progressBar.style.display = 'block';

            const formData = new FormData();
            uploadedFiles.forEach(file => formData.append('files', file));

            // Add configuration
            formData.append('date_format', document.getElementById('dateFormat').value);
            formData.append('currency', document.getElementById('currency').value);
            formData.append('include_metadata', document.getElementById('includeMetadata').checked);

            try {
                progressBarInner.style.width = '30%';

                const response = await fetch('/api/transform', {
                    method: 'POST',
                    body: formData
                });

                progressBarInner.style.width = '90%';
                const result = await response.json();
                progressBarInner.style.width = '100%';

                displayResults(result);

            } catch (error) {
                console.error('Error:', error);
                alert('Processing failed: ' + error.message);
            } finally {
                uploadBtn.disabled = false;
                uploadBtn.textContent = 'Transform Files';
                setTimeout(() => {
                    progressBar.style.display = 'none';
                }, 1000);
            }
        }

        function displayResults(result) {
            const fileResultsDiv = document.getElementById('fileResults');

            if (result.success) {
                fileResultsDiv.innerHTML = `
                    <h4 class="success">✅ Processing Complete!</h4>
                    ${result.results.map(fileResult => `
                        <div class="file-item">
                            <div>
                                <strong>${fileResult.metadata?.file_name || fileResult.file_name || 'Unknown'}</strong><br>
                                <small>${fileResult.success ? 
                                    `${fileResult.records_processed} records processed (${fileResult.original_format})` : 
                                    `Error: ${fileResult.error}`
                                }</small>
                            </div>
                            <div>
                                <span class="status-badge ${fileResult.success ? 'status-success' : 'status-error'}">
                                    ${fileResult.success ? 'Success' : 'Failed'}
                                </span>
                                ${fileResult.success && fileResult.output_file ? 
                                    `<button class="btn btn-preview btn-small" onclick="previewFile('${fileResult.output_file}', '${fileResult.metadata?.file_name || fileResult.file_name}')">👁️ Preview</button>
                                     <button class="btn btn-download btn-small" onclick="downloadFile('${fileResult.output_file}')">📥 Download</button>` : 
                                    ''
                                }
                            </div>
                        </div>
                    `).join('')}
                `;
            } else {
                fileResultsDiv.innerHTML = `
                    <div class="error">❌ Processing failed: ${result.error}</div>
                `;
            }
        }

        async function previewFile(fileName, originalName) {
            const modal = document.getElementById('previewModal');
            const content = document.getElementById('previewContent');

            // Show modal with loading
            modal.style.display = 'block';
            content.innerHTML = `
                <div class="loading">
                    <div class="spinner"></div>
                    <p>Loading preview for ${originalName}...</p>
                </div>
            `;

            try {
                const response = await fetch(`/api/preview/${encodeURIComponent(fileName)}`);
                const result = await response.json();

                if (result.success) {
                    content.innerHTML = `
                        <div class="preview-info">
                            <h4>📄 ${originalName}</h4>
                            <p><strong>Format:</strong> ${result.format} → Standardized</p>
                            <p><strong>Total Records:</strong> ${result.total_records}</p>
                            <p><strong>Account:</strong> ${result.account_info.account_name || 'N/A'} (${result.account_info.account_number || 'N/A'})</p>
                            <p><strong>Date Range:</strong> ${result.date_range || 'N/A'}</p>
                            <p><em>Showing first 20 transactions:</em></p>
                        </div>
                        <div style="overflow-x: auto;">
                            <table class="preview-table">
                                <thead>
                                    <tr>
                                        ${result.headers.map(header => `<th>${header}</th>`).join('')}
                                    </tr>
                                </thead>
                                <tbody>
                                    ${result.data.map(row => 
                                        `<tr>${result.headers.map(header => `<td>${row[header] || ''}</td>`).join('')}</tr>`
                                    ).join('')}
                                </tbody>
                            </table>
                        </div>
                        ${result.total_records > 20 ? `<p style="margin-top: 15px; color: #666;"><em>... and ${result.total_records - 20} more transactions. Download the full file to see all records.</em></p>` : ''}
                    `;
                } else {
                    content.innerHTML = `
                        <div class="error">❌ Failed to load preview: ${result.error}</div>
                    `;
                }
            } catch (error) {
                content.innerHTML = `
                    <div class="error">❌ Failed to load preview: ${error.message}</div>
                `;
            }
        }

        function closePreview() {
            document.getElementById('previewModal').style.display = 'none';
        }

        // Close modal when clicking outside
        window.onclick = function(event) {
            const modal = document.getElementById('previewModal');
            if (event.target === modal) {
                modal.style.display = 'none';
            }
        }

        function downloadFile(fileName) {
            const downloadUrl = `/api/download/${encodeURIComponent(fileName)}`;
            console.log('Downloading:', downloadUrl);

            // Create invisible download link
            const link = document.createElement('a');
            link.href = downloadUrl;
            link.download = fileName;
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
        }
    </script>
</body>
</html>
"""


@app.route('/')
def index():
    """Main page"""
    return render_template_string(HTML_TEMPLATE)


@app.route('/api/transform', methods=['POST'])
def transform_statements():
    """API endpoint to transform bank statements"""
    try:
        if 'files' not in request.files:
            return jsonify({'success': False, 'error': 'No files uploaded'})

        files = request.files.getlist('files')
        if not files or all(file.filename == '' for file in files):
            return jsonify({'success': False, 'error': 'No files selected'})

        # Get configuration options
        options = {
            'date_format': request.form.get('date_format', 'DD/MM/YYYY'),
            'currency': request.form.get('currency', 'NGN'),
            'include_metadata': request.form.get('include_metadata', 'false').lower() == 'true'
        }

        results = []

        for file in files:
            if file and allowed_file(file.filename):
                try:
                    # Save uploaded file temporarily
                    filename = secure_filename(file.filename)
                    unique_filename = f"{uuid.uuid4()}_{filename}"
                    file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
                    file.save(file_path)

                    logger.info(f"Processing file: {file_path}")

                    # Process the file
                    result = transformer.transform_statement(file_path, options)

                    if result['success']:
                        # Generate standardized output file
                        output_filename = f"standardized_{filename}"
                        output_path = os.path.join(app.config['UPLOAD_FOLDER'], output_filename)

                        logger.info(f"Generating output file: {output_path}")

                        # Generate the standardized file
                        transformer.generate_standardized_file(result, output_path, options)

                        # Verify file was created
                        if os.path.exists(output_path):
                            result['output_file'] = output_filename
                            result['download_ready'] = True
                            file_size = os.path.getsize(output_path)
                            logger.info(f"✅ Generated standardized file: {output_path} ({file_size} bytes)")
                        else:
                            logger.error(f"❌ Failed to generate output file: {output_path}")
                            result['success'] = False
                            result['error'] = "Failed to generate standardized file"

                    results.append(result)

                    # Clean up input file
                    if os.path.exists(file_path):
                        os.remove(file_path)

                except Exception as e:
                    logger.error(f"Error processing file {file.filename}: {str(e)}")
                    results.append({
                        'success': False,
                        'error': str(e),
                        'file_name': file.filename
                    })
            else:
                results.append({
                    'success': False,
                    'error': 'Invalid file format',
                    'file_name': file.filename if file else 'Unknown'
                })

        return jsonify({
            'success': True,
            'results': results,
            'total_processed': len([r for r in results if r['success']]),
            'total_failed': len([r for r in results if not r['success']])
        })

    except Exception as e:
        logger.error(f"Transformation API error: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/preview/<filename>')
def preview_file(filename):
    """Preview processed file"""
    try:
        # Clean the filename for security
        filename = secure_filename(filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)

        logger.info(f"Preview request for: {filename}")

        if not os.path.exists(file_path):
            return jsonify({'success': False, 'error': 'File not found'}), 404

        # Read the Excel file
        try:
            # Read both sheets if they exist
            excel_file = pd.ExcelFile(file_path)
            sheet_names = excel_file.sheet_names

            # Read the transactions sheet
            if 'Transactions' in sheet_names:
                df = pd.read_excel(file_path, sheet_name='Transactions')
            else:
                df = pd.read_excel(file_path, sheet_name=0)  # First sheet

            # Read metadata if available
            account_info = {}
            format_info = "Standardized"

            if 'Metadata' in sheet_names:
                try:
                    metadata_df = pd.read_excel(file_path, sheet_name='Metadata')
                    for _, row in metadata_df.iterrows():
                        field = str(row.iloc[0]).strip()
                        value = str(row.iloc[1]).strip() if len(row) > 1 else ''

                        if 'Account Number' in field:
                            account_info['account_number'] = value
                        elif 'Account Name' in field:
                            account_info['account_name'] = value
                        elif 'Original Format' in field:
                            format_info = value
                except Exception as e:
                    logger.warning(f"Could not read metadata: {e}")

            # Get preview data (first 20 rows)
            preview_rows = min(20, len(df))
            preview_df = df.head(preview_rows)

            # Convert to records for JSON
            headers = list(df.columns)
            data = preview_df.to_dict('records')

            # Clean the data (replace NaN with empty strings)
            for row in data:
                for key in row:
                    if pd.isna(row[key]):
                        row[key] = ''
                    else:
                        row[key] = str(row[key])

            # Try to determine date range
            date_range = "N/A"
            try:
                if 'Tran Date' in df.columns:
                    dates = pd.to_datetime(df['Tran Date'], errors='coerce').dropna()
                    if len(dates) > 0:
                        min_date = dates.min().strftime('%d/%m/%Y')
                        max_date = dates.max().strftime('%d/%m/%Y')
                        date_range = f"{min_date} to {max_date}"
            except Exception as e:
                logger.warning(f"Could not determine date range: {e}")

            return jsonify({
                'success': True,
                'headers': headers,
                'data': data,
                'total_records': len(df),
                'preview_records': preview_rows,
                'account_info': account_info,
                'format': format_info,
                'date_range': date_range
            })

        except Exception as e:
            logger.error(f"Error reading Excel file: {e}")
            return jsonify({'success': False, 'error': f'Could not read file: {str(e)}'}), 500

    except Exception as e:
        logger.error(f"Preview error: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/download/<filename>')
def download_file(filename):
    """Download processed file"""
    try:
        # Clean the filename for security
        filename = secure_filename(filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)

        logger.info(f"Download request for: {filename}")
        logger.info(f"Full path: {file_path}")
        logger.info(f"File exists: {os.path.exists(file_path)}")

        if os.path.exists(file_path):
            logger.info(f"✅ Sending file: {file_path}")
            return send_file(
                file_path,
                as_attachment=True,
                download_name=filename,
                mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            )
        else:
            # List available files for debugging
            available_files = []
            if os.path.exists(app.config['UPLOAD_FOLDER']):
                available_files = os.listdir(app.config['UPLOAD_FOLDER'])

            logger.error(f"❌ File not found. Requested: {filename}")
            logger.error(f"Available files in {app.config['UPLOAD_FOLDER']}: {available_files}")

            return jsonify({
                'error': 'File not found',
                'requested': filename,
                'upload_folder': app.config['UPLOAD_FOLDER'],
                'available': available_files
            }), 404

    except Exception as e:
        logger.error(f"Download error: {str(e)}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/health')
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'transformer': 'initialized',
        'supported_formats': list(ALLOWED_EXTENSIONS),
        'upload_folder': app.config['UPLOAD_FOLDER'],
        'upload_folder_exists': os.path.exists(app.config['UPLOAD_FOLDER'])
    })


@app.route('/api/debug')
def debug_info():
    """Debug endpoint to check file system"""
    try:
        upload_folder = app.config['UPLOAD_FOLDER']
        files_in_folder = []

        if os.path.exists(upload_folder):
            files_in_folder = os.listdir(upload_folder)

        return jsonify({
            'upload_folder': upload_folder,
            'folder_exists': os.path.exists(upload_folder),
            'files_in_folder': files_in_folder,
            'total_files': len(files_in_folder)
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    print("🚀 Starting Nigerian Bank Statement Transformer...")
    print("📊 Supported formats: XLSX, XLS, ODS")
    print(f"📁 Upload folder: {app.config['UPLOAD_FOLDER']}")
    print("🔗 Access the application at: http://localhost:5000")
    print("⚙️  Health check available at: http://localhost:5000/api/health")
    print("🐛 Debug info available at: http://localhost:5000/api/debug")
    print("👁️  Preview feature enabled!")

    # Ensure upload folder exists
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

    # Run the application
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=True,  # Set to False in production
        threaded=True
    )