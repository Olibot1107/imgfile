# File Compressor - Version 8.3

A high-performance tool for compressing folders into PNG images and extracting them back. Includes CLI, GUI, and a production-ready REST API server.

## Features

- **Multiple Interfaces**: CLI, GUI, and REST API server
- **Compression Methods**: LZMA, BZIP2, ZLIB, ZIP-LZMA, ZIP-BZIP2
- **Encryption**: Optional password protection
- **Stateless API**: No file storage, immediate response delivery
- **API Authentication**: Secure your public endpoints with API keys
- **High Performance**: Gzip compression, async cleanup, optimized defaults

## Quick Start

### Install Dependencies

**Windows:**

```bash
start.bat 4
```

**Linux:**

```bash
sudo apt install python3-pip
chmod +x start.sh
./start.sh 4
```

## Usage

### CLI Mode

```bash
# Windows
start.bat 1

# Linux
./start.sh 1
```

### GUI Mode

```bash
# Windows
start.bat 2

# Linux
./start.sh 2
```

### API Server

**Without Authentication (Development):**

```bash
# Windows
start.bat 3

# Linux
./start.sh 3
```

**With Authentication (Production):**

```bash
# Windows PowerShell
$env:API_KEY="your-secret-key-here"
python server.py

# Linux/Mac
export API_KEY="your-secret-key-here"
python server.py
```

## API Documentation

### Endpoints

**POST /api/compress** - Compress files to PNG

- **Headers**: `X-API-Key` (if authentication enabled)
- **Form Data**:
  - `files`: Multiple file uploads (required)
  - `compression_method`: lzma|bz2|zlib|zip_lzma|zip_bz2 (default: zlib)
  - `enable_limit`: true|false (default: true)
  - `password`: Optional encryption password
- **Returns**: PNG file

**POST /api/extract** - Extract PNG to files

- **Headers**: `X-API-Key` (if authentication enabled)
- **Form Data**:
  - `file`: PNG file (required)
  - `password`: Optional decryption password
- **Returns**: ZIP file

**POST /api/info** - Get PNG file information

- **Headers**: `X-API-Key` (if authentication enabled)
- **Form Data**: `file`: PNG file (required)
- **Returns**: JSON metadata

**GET /api/methods** - List compression methods

- **Returns**: JSON array of available methods

### API Usage Example

```python
import requests

# Set API key if authentication is enabled
headers = {'X-API-Key': 'your-secret-key-here'}

# Compress files
files = {'files': [open('file1.txt', 'rb'), open('file2.txt', 'rb')]}
response = requests.post('http://localhost:4362/api/compress',
                        files=files,
                        headers=headers)

with open('output.png', 'wb') as f:
    f.write(response.content)

# Extract files
files = {'file': open('output.png', 'rb')}
response = requests.post('http://localhost:4362/api/extract',
                        files=files,
                        headers=headers)

with open('extracted.zip', 'wb') as f:
    f.write(response.content)
```

## Performance Features

- **Gzip Compression**: Automatic response compression
- **Async Cleanup**: Non-blocking temporary file cleanup
- **Optimized Defaults**: Fast zlib compression by default
- **Streaming**: Efficient file transfer for large files
- **Comprehensive Logging**: Detailed logs in console and `server.log`

## Security

### API Authentication

Set the `API_KEY` environment variable to enable authentication:

- All `/api/*` endpoints require `X-API-Key` header
- Returns 401 Unauthorized for missing/invalid keys
- Logs all authentication attempts with client IP

### File Encryption

Use the `password` parameter to encrypt compressed files with AES-256.

## Autorun Script

If a PNG contains `autorun.bat`, `autorun.sh`, or `autorun.py`, the user will be prompted to run it upon extraction.

## License

Apache License 2.0

## Contributing

Contributions welcome! Open an issue or submit a pull request.
