import os
import io
import time
import shutil
import logging
import tempfile
import zipfile
import threading
import hmac
from functools import wraps
from flask import Flask, request, jsonify, send_file
from flask_compress import Compress
from flask_cors import CORS
from werkzeug.utils import secure_filename
from encoder import encode_folder_to_png
from decoder import decode_png_to_folder, get_decode_info

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('server.log')
    ]
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)
Compress(app)  # Enable gzip compression for responses

# Load API key from environment variable
API_KEY = os.environ.get('API_KEY', None)
app.config['MAX_CONTENT_LENGTH'] = 200 * 1024 * 1024 # lets not get DOSd gng

if API_KEY:
    logger.info("API authentication enabled")
else:
    logger.warning("No API_KEY set - server is running without authentication!")

def require_api_key(f):
    """Decorator to require API key authentication"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not API_KEY:
            # No API key configured, allow access
            return f(*args, **kwargs)
        
        # Check for API key in header
        provided_key = request.headers.get('X-API-Key')
        
        if not provided_key:
            logger.warning(f"Unauthorized access attempt from {request.remote_addr}")
            return jsonify({'error': 'API key required. Provide X-API-Key header.'}), 401
        # some skinny twat could try and find the key based on timings so
        if not hmac.compare_digest(provided_key, API_KEY):
            logger.warning(f"Invalid API key from {request.remote_addr}")
            return jsonify({'error': 'Invalid API key'}), 401
        
        return f(*args, **kwargs)
    
    return decorated_function

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    logger.info("Health check requested")
    return jsonify({'status': 'ok', 'message': 'File Compressor API is running'})

def cleanup_temp_dir_async(temp_dir):
    """Async cleanup of temporary directory"""
    def cleanup():
        try:
            time.sleep(0.5)  # Small delay to ensure file handles are released
            shutil.rmtree(temp_dir)
            logger.info(f"Cleaned up temp directory: {temp_dir}")
        except Exception as e:
            logger.error(f"Failed to clean up temp directory {temp_dir}: {e}")
    
    thread = threading.Thread(target=cleanup, daemon=True)
    thread.start()

@app.route('/api/compress', methods=['POST'])
@require_api_key
def compress_folder():
    """
    Compress a folder to PNG synchronously
    """
    start_time = time.time()
    temp_dir = tempfile.mkdtemp(prefix='compress_')
    logger.info(f"[{request.remote_addr}] Starting compression request. Temp dir: {temp_dir}")
    
    try:
        if 'files' not in request.files:
            logger.error("No files provided in request")
            cleanup_temp_dir_async(temp_dir)
            return jsonify({'error': 'No files provided'}), 400
        
        files = request.files.getlist('files')
        ALLOWED = {'zlib','lzma','bz2','zip_lzma','zip_bz2'}
        compression_method = request.form.get('compression_method', 'zlib')  # Changed default to zlib for speed
        if compression_method not in ALLOWED:
            return jsonify({'error':'invalid compression method'}), 400 # we ant blindly accepting the method gng

        enable_limit = request.form.get('enable_limit', 'true').lower() == 'true'
        password = request.form.get('password', None)
        
        if password == '':
            password = None
            
        logger.info(f"Processing {len(files)} files. Method: {compression_method}, Password: {'Yes' if password else 'No'}")
        
        # Create input directory for files
        input_dir = os.path.join(temp_dir, 'input')
        os.makedirs(input_dir, exist_ok=True)
        
        # Save uploaded files with streaming
        for file in files:
            if file.filename:
                filepath = secure_filename(file.filename)
                filepath = filepath.replace('/', os.sep)
                filepath = os.path.basename(filepath) # they aint getting past this shi
                full_path = os.path.join(input_dir, filepath)
                os.makedirs(os.path.dirname(full_path), exist_ok=True)
                file.save(full_path)
                logger.debug(f"Saved file: {filepath}")
        
        # Output file path
        output_filename = f'compressed_{int(time.time())}.png'
        output_path = os.path.join(temp_dir, output_filename)
        
        # Define callbacks for logging
        def log_callback(msg):
            logger.info(f"[Encoder] {msg}")
            
        def progress_callback(percent, message=''):
            logger.info(f"[Encoder Progress] {percent:.1f}% - {message}")

        # Run compression
        logger.info("Starting encoding process...")
        encode_folder_to_png(
            input_dir,
            output_path,
            compression_method,
            progress_callback,
            enable_limit,
            password,
            log_callback
        )
        logger.info("Encoding complete.")
        
        # Stream the file back
        duration = time.time() - start_time
        logger.info(f"Request completed in {duration:.2f}s")
        
        # Use send_file with path for better streaming
        response = send_file(
            output_path,
            mimetype='image/png',
            as_attachment=True,
            download_name=output_filename
        )
        
        # Schedule async cleanup after response is sent
        cleanup_temp_dir_async(temp_dir)
        
        return response

    except Exception as e:
        logger.error(f"Error during compression: {e}", exc_info=True)
        cleanup_temp_dir_async(temp_dir)
        # cant expose the errors to these bitches
        return jsonify({'error': 'Internal Server Error'}), 500
        

@app.route('/api/extract', methods=['POST'])
@require_api_key
def extract_png():
    """
    Extract PNG to folder synchronously
    """
    start_time = time.time()
    temp_dir = tempfile.mkdtemp(prefix='extract_')
    logger.info(f"[{request.remote_addr}] Starting extraction request. Temp dir: {temp_dir}")
    
    try:
        if 'file' not in request.files:
            logger.error("No file provided")
            cleanup_temp_dir_async(temp_dir)
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        password = request.form.get('password', None)
        
        if password == '':
            password = None
            
        # Save input PNG
        input_png = os.path.join(temp_dir, 'input.png')
        file.save(input_png)
        logger.info(f"Saved input PNG. Size: {os.path.getsize(input_png)} bytes")
        
        # Output directory
        output_dir = os.path.join(temp_dir, 'output')
        os.makedirs(output_dir, exist_ok=True)
        
        # Callbacks
        def log_callback(msg):
            logger.info(f"[Decoder] {msg}")
            
        def progress_callback(percent, message='', file='', start_offset=0, end_offset=0):
            logger.info(f"[Decoder Progress] {percent:.1f}% - {message}")

        # Run decoding
        logger.info("Starting decoding process...")
        decode_png_to_folder(
            input_png,
            output_dir,
            progress_callback,
            password,
            log_callback
        )
        logger.info("Decoding complete.")
        
        # Zip the output with optimized settings
        zip_filename = f'extracted_{int(time.time())}.zip'
        zip_path = os.path.join(temp_dir, zip_filename)
        
        logger.info("Creating ZIP file...")
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED, compresslevel=6) as zipf:
            for root, dirs, files in os.walk(output_dir):
                for f in files:
                    file_path = os.path.join(root, f)
                    arcname = os.path.relpath(file_path, output_dir)
                    zipf.write(file_path, arcname)
        
        duration = time.time() - start_time
        logger.info(f"Request completed in {duration:.2f}s")
        
        # Stream back
        response = send_file(
            zip_path,
            mimetype='application/zip',
            as_attachment=True,
            download_name=zip_filename
        )
        
        # Schedule async cleanup
        cleanup_temp_dir_async(temp_dir)
        
        return response

    except Exception as e:
        logger.error(f"Error during extraction: {e}", exc_info=True)
        cleanup_temp_dir_async(temp_dir)
        return jsonify({'error': str(e)}), 500

@app.route('/api/info', methods=['POST'])
@require_api_key
def get_info():
    """
    Get information about a PNG file
    """
    temp_dir = tempfile.mkdtemp(prefix='info_')
    logger.info(f"[{request.remote_addr}] Info request. Temp dir: {temp_dir}")
    
    try:
        if 'file' not in request.files:
            cleanup_temp_dir_async(temp_dir)
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        temp_png = os.path.join(temp_dir, 'temp.png')
        file.save(temp_png)
        
        from PIL import Image
        Image.MAX_IMAGE_PIXELS = 50_000_000 # lets not get image bombed gng
        folder_name, file_count, total_size, compression_method, password_info, metadata_channels = get_decode_info(temp_png)
        
        img = Image.open(temp_png)
        img.verify()
        with Image.open(temp_png) as img: # lets us not decode the whole fuckass image
            width, height = img.size
        
        cleanup_temp_dir_async(temp_dir)
        
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
        logger.error(f"Error getting info: {e}", exc_info=True)
        cleanup_temp_dir_async(temp_dir)
        return jsonify({'error': str(e)}), 500

@app.route('/api/methods', methods=['GET'])
def get_compression_methods():
    """Get available compression methods"""
    methods = [
        {'value': 'zlib', 'name': 'ZLIB (Fast compression)', 'recommended': True},
        {'value': 'lzma', 'name': 'LZMA (Best compression)'},
        {'value': 'bz2', 'name': 'BZIP2 (Good compression)'},
        {'value': 'zip_lzma', 'name': 'ZIP-LZMA (Compatible)'},
        {'value': 'zip_bz2', 'name': 'ZIP-BZIP2 (Compatible)'}
    ]
    return jsonify({'methods': methods})

@app.route('/', methods=['GET'])
def index():
    """API documentation"""
    auth_status = "ENABLED" if API_KEY else "DISABLED"
    auth_note = "<p><strong>Authentication:</strong> API key required via X-API-Key header</p>" if API_KEY else "<p><strong>Warning:</strong> No authentication configured</p>"
    
    return f"""
    <html>
    <head><title>File Compressor API</title></head>
    <body style="font-family: Arial, sans-serif; max-width: 800px; margin: 50px auto; padding: 20px;">
        <h1>File Compressor API (Stateless & Optimized)</h1>
        <p>High-performance synchronous Web API for compressing folders to PNG and extracting them back.</p>
        
        <p><strong>Authentication Status:</strong> {auth_status}</p>
        {auth_note}
        
        <h2>Endpoints</h2>
        
        <h3>POST /api/compress</h3>
        <p>Compress files to PNG. Returns the PNG file directly.</p>
        <p><em>Headers:</em> X-API-Key (if authentication enabled)</p>
        
        <h3>POST /api/extract</h3>
        <p>Extract PNG to files. Returns a ZIP file directly.</p>
        <p><em>Headers:</em> X-API-Key (if authentication enabled)</p>
        
        <h3>POST /api/info</h3>
        <p>Get information about a PNG file.</p>
        <p><em>Headers:</em> X-API-Key (if authentication enabled)</p>
        
        <h3>GET /api/methods</h3>
        <p>Get available compression methods.</p>
        
        <h2>Performance Features</h2>
        <ul>
            <li>Gzip compression for API responses</li>
            <li>Async cleanup of temporary files</li>
            <li>Optimized default compression (zlib)</li>
            <li>Streaming file transfers</li>
        </ul>
    </body>
    </html>
    """

if __name__ == '__main__':
    print("Starting File Compressor API on http://0.0.0.0:4362")
    if API_KEY:
        print("✓ API authentication enabled")
    else:
        print("⚠ WARNING: No API_KEY environment variable set - server is UNPROTECTED!")
        print("  Set API_KEY environment variable to enable authentication")
    app.run(host='0.0.0.0', port=4362, debug=False, threaded=True)
