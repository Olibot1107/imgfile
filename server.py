from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import os
import io
import base64
import tempfile
import shutil
import zipfile
from werkzeug.utils import secure_filename
from encoder import encode_folder_to_png
from decoder import decode_png_to_folder, get_decode_info
import threading
import time
from PIL import Image

app = Flask(__name__)
CORS(app)

# Configure upload folder
UPLOAD_FOLDER = 'tmp/uploads'
OUTPUT_FOLDER = 'tmp/outputs'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

# Store progress data for async operations
progress_data = {}

def cleanup_old_files():
    """Clean up files older than 1 hour"""
    for folder in [UPLOAD_FOLDER, OUTPUT_FOLDER]:
        for filename in os.listdir(folder):
            filepath = os.path.join(folder, filename)
            if os.path.isfile(filepath):
                if time.time() - os.path.getmtime(filepath) > 3600:
                    try:
                        os.remove(filepath)
                    except:
                        pass
            elif os.path.isdir(filepath):
                if time.time() - os.path.getmtime(filepath) > 3600:
                    try:
                        shutil.rmtree(filepath)
                    except:
                        pass

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({'status': 'ok', 'message': 'File Compressor API is running'})

@app.route('/api/compress', methods=['POST'])
def compress_folder():
    """
    Compress a folder to PNG
    
    Request body:
    - files: Multiple file uploads
    - folder_structure: JSON mapping of file paths (optional)
    - compression_method: lzma, bz2, zlib, zip_lzma, zip_bz2 (default: lzma)
    - enable_limit: boolean (default: true)
    - password: string (optional)
    """
    try:
        cleanup_old_files()
        
        if 'files' not in request.files:
            return jsonify({'error': 'No files provided'}), 400
        
        files = request.files.getlist('files')
        compression_method = request.form.get('compression_method', 'lzma')
        enable_limit = request.form.get('enable_limit', 'true').lower() == 'true'
        password = request.form.get('password', None)
        
        if password == '':
            password = None
        
        # Create a temporary folder to store uploaded files
        temp_folder = os.path.join(UPLOAD_FOLDER, f'compress_{int(time.time())}')
        os.makedirs(temp_folder, exist_ok=True)
        
        # Save uploaded files
        for file in files:
            if file.filename:
                # Handle folder structure if provided
                filepath = secure_filename(file.filename)
                # Replace forward slashes with os separator
                filepath = filepath.replace('/', os.sep)
                full_path = os.path.join(temp_folder, filepath)
                
                # Create subdirectories if needed
                os.makedirs(os.path.dirname(full_path), exist_ok=True)
                file.save(full_path)
        
        # Generate output PNG path
        output_filename = f'compressed_{int(time.time())}.png'
        output_path = os.path.join(OUTPUT_FOLDER, output_filename)
        
        # Progress tracking
        job_id = str(int(time.time() * 1000))
        progress_data[job_id] = {'progress': 0, 'message': 'Starting compression', 'status': 'running'}
        
        def progress_callback(percent, message=''):
            progress_data[job_id] = {
                'progress': percent,
                'message': message,
                'status': 'running'
            }
        
        def log_callback(msg):
            if job_id in progress_data:
                progress_data[job_id]['last_log'] = msg
        
        # Encode in background thread
        def encode_task():
            try:
                encode_folder_to_png(
                    temp_folder,
                    output_path,
                    compression_method,
                    progress_callback,
                    enable_limit,
                    password,
                    log_callback
                )
                progress_data[job_id] = {
                    'progress': 100,
                    'message': 'Compression complete',
                    'status': 'complete',
                    'output_file': output_filename
                }
            except Exception as e:
                progress_data[job_id] = {
                    'progress': 0,
                    'message': str(e),
                    'status': 'error'
                }
            finally:
                # Cleanup temp folder
                try:
                    shutil.rmtree(temp_folder)
                except:
                    pass
        
        thread = threading.Thread(target=encode_task, daemon=True)
        thread.start()
        
        return jsonify({
            'job_id': job_id,
            'message': 'Compression started',
            'status': 'running'
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/extract', methods=['POST'])
def extract_png():
    """
    Extract PNG to folder
    
    Request body:
    - file: PNG file upload
    - password: string (optional)
    """
    try:
        cleanup_old_files()
        
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        password = request.form.get('password', None)
        
        if password == '':
            password = None
        
        # Save uploaded PNG
        temp_png = os.path.join(UPLOAD_FOLDER, f'extract_{int(time.time())}.png')
        file.save(temp_png)
        
        # Create output folder
        output_folder = os.path.join(OUTPUT_FOLDER, f'extracted_{int(time.time())}')
        os.makedirs(output_folder, exist_ok=True)
        
        # Progress tracking
        job_id = str(int(time.time() * 1000))
        progress_data[job_id] = {'progress': 0, 'message': 'Starting extraction', 'status': 'running'}
        
        def progress_callback(percent, message='', file='', start_offset=0, end_offset=0):
            progress_data[job_id] = {
                'progress': percent,
                'message': message,
                'status': 'running',
                'current_file': file
            }
        
        def log_callback(msg):
            if job_id in progress_data:
                progress_data[job_id]['last_log'] = msg
        
        # Decode in background thread
        def decode_task():
            try:
                decode_png_to_folder(
                    temp_png,
                    output_folder,
                    progress_callback,
                    password,
                    log_callback
                )
                
                # Create a zip of extracted files for download
                zip_filename = f'extracted_{int(time.time())}.zip'
                zip_path = os.path.join(OUTPUT_FOLDER, zip_filename)
                
                with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                    for root, dirs, files in os.walk(output_folder):
                        for f in files:
                            file_path = os.path.join(root, f)
                            arcname = os.path.relpath(file_path, output_folder)
                            zipf.write(file_path, arcname)
                
                progress_data[job_id] = {
                    'progress': 100,
                    'message': 'Extraction complete',
                    'status': 'complete',
                    'output_file': zip_filename
                }
            except Exception as e:
                progress_data[job_id] = {
                    'progress': 0,
                    'message': str(e),
                    'status': 'error'
                }
            finally:
                # Cleanup temp files
                try:
                    os.remove(temp_png)
                    shutil.rmtree(output_folder)
                except:
                    pass
        
        thread = threading.Thread(target=decode_task, daemon=True)
        thread.start()
        
        return jsonify({
            'job_id': job_id,
            'message': 'Extraction started',
            'status': 'running'
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/info', methods=['POST'])
def get_info():
    """
    Get information about a PNG file without extracting
    
    Request body:
    - file: PNG file upload
    """
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        
        # Save uploaded PNG temporarily
        temp_png = os.path.join(UPLOAD_FOLDER, f'info_{int(time.time())}.png')
        file.save(temp_png)
        
        # Get info
        folder_name, file_count, total_size, compression_method, password_info, metadata_channels = get_decode_info(temp_png)
        
        # Get image dimensions
        img = Image.open(temp_png)
        width, height = img.size
        
        # Cleanup
        os.remove(temp_png)
        
        return jsonify({
            'folder_name': folder_name,
            'file_count': file_count,
            'total_size': total_size,
            'total_size_mb': round(total_size / (1024 * 1024), 2),
            'compression_method': compression_method,
            'password_protected': password_info == 'encrypted',
            'image_width': width,
            'image_height': height,
            'metadata_channels': metadata_channels
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/progress/<job_id>', methods=['GET'])
def get_progress(job_id):
    """Get progress of a compression or extraction job"""
    if job_id not in progress_data:
        return jsonify({'error': 'Job not found'}), 404
    
    return jsonify(progress_data[job_id])

@app.route('/api/download/<filename>', methods=['GET'])
def download_file(filename):
    """Download a generated file"""
    try:
        filepath = os.path.join(OUTPUT_FOLDER, secure_filename(filename))
        
        if not os.path.exists(filepath):
            return jsonify({'error': 'File not found'}), 404
        
        return send_file(
            filepath,
            as_attachment=True,
            download_name=filename
        )
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/preview/<filename>', methods=['GET'])
def preview_image(filename):
    """Get a preview/thumbnail of a PNG file"""
    try:
        filepath = os.path.join(OUTPUT_FOLDER, secure_filename(filename))
        
        if not os.path.exists(filepath):
            return jsonify({'error': 'File not found'}), 404
        
        # Create thumbnail
        img = Image.open(filepath)
        img.thumbnail((800, 800), Image.Resampling.LANCZOS)
        
        # Convert to base64
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        buffer.seek(0)
        img_base64 = base64.b64encode(buffer.read()).decode()
        
        return jsonify({
            'image': f'data:image/png;base64,{img_base64}',
            'width': img.width,
            'height': img.height
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/methods', methods=['GET'])
def get_compression_methods():
    """Get available compression methods"""
    methods = [
        {'value': 'lzma', 'name': 'LZMA (Best compression)'},
        {'value': 'bz2', 'name': 'BZIP2 (Good compression)'},
        {'value': 'zlib', 'name': 'ZLIB (Fast compression)'},
        {'value': 'zip_lzma', 'name': 'ZIP-LZMA (Compatible)'},
        {'value': 'zip_bz2', 'name': 'ZIP-BZIP2 (Compatible)'}
    ]
    return jsonify({'methods': methods})

@app.route('/', methods=['GET'])
def index():
    """API documentation"""
    docs = """
    <html>
    <head><title>File Compressor API</title></head>
    <body style="font-family: Arial, sans-serif; max-width: 800px; margin: 50px auto; padding: 20px;">
        <h1>File Compressor API v8.0</h1>
        <p>Web API for compressing folders to PNG and extracting them back.</p>
        
        <h2>Endpoints</h2>
        
        <h3>GET /health</h3>
        <p>Health check endpoint</p>
        
        <h3>POST /api/compress</h3>
        <p>Compress files to PNG</p>
        <p><strong>Form Data:</strong></p>
        <ul>
            <li><code>files</code>: Multiple file uploads (required)</li>
            <li><code>compression_method</code>: lzma|bz2|zlib|zip_lzma|zip_bz2 (default: lzma)</li>
            <li><code>enable_limit</code>: true|false (default: true)</li>
            <li><code>password</code>: Optional password for encryption</li>
        </ul>
        <p><strong>Returns:</strong> JSON with job_id for progress tracking</p>
        
        <h3>POST /api/extract</h3>
        <p>Extract PNG to files</p>
        <p><strong>Form Data:</strong></p>
        <ul>
            <li><code>file</code>: PNG file upload (required)</li>
            <li><code>password</code>: Optional password for decryption</li>
        </ul>
        <p><strong>Returns:</strong> JSON with job_id for progress tracking</p>
        
        <h3>POST /api/info</h3>
        <p>Get information about a PNG file</p>
        <p><strong>Form Data:</strong></p>
        <ul>
            <li><code>file</code>: PNG file upload (required)</li>
        </ul>
        <p><strong>Returns:</strong> JSON with file information</p>
        
        <h3>GET /api/progress/{job_id}</h3>
        <p>Get progress of compression/extraction job</p>
        <p><strong>Returns:</strong> JSON with progress percentage and status</p>
        
        <h3>GET /api/download/{filename}</h3>
        <p>Download a generated file</p>
        
        <h3>GET /api/preview/{filename}</h3>
        <p>Get base64 preview of PNG file</p>
        
        <h3>GET /api/methods</h3>
        <p>Get available compression methods</p>
        
        <hr>
        <p><em>Made by Olibot13 and ChatGPT</em></p>
    </body>
    </html>
    """
    return docs

if __name__ == '__main__':
    print("Starting File Compressor API on http://0.0.0.0:4362")
    print("API Documentation: http://localhost:4362/")
    app.run(host='0.0.0.0', port=4362, debug=False, threaded=True)
