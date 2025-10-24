from PIL import Image
import os, zipfile, math, sys, tempfile, traceback, lzma, bz2, hashlib, secrets

def encode_folder_to_png(folder_path, output_png, compression_method='lzma', password=None, progress_callback=None):
    """Compress a folder into a PNG image file with enhanced compression

    Args:
        folder_path: Path to the folder to compress
        output_png: Output PNG file path
        compression_method: Compression algorithm to use ('lzma', 'bz2', 'zlib', 'zip_lzma', 'zip_bz2')
    """
    try:
        if not os.path.exists(folder_path):
            raise FileNotFoundError(f"Folder not found: {folder_path}")

        if not os.path.isdir(folder_path):
            raise NotADirectoryError(f"Path is not a directory: {folder_path}")

        
        print(f"Creating compressed archive from '{folder_path}' using {compression_method}...")

        with tempfile.NamedTemporaryFile(suffix='.zip', delete=False) as tmp_zip:
            zip_path = tmp_zip.name

        try:
            
            if compression_method == 'lzma':
                compression_type = zipfile.ZIP_LZMA
            elif compression_method == 'bz2':
                compression_type = zipfile.ZIP_BZIP2
            elif compression_method == 'zlib':
                compression_type = zipfile.ZIP_DEFLATED
            elif compression_method == 'zip_lzma':
                compression_type = zipfile.ZIP_LZMA
            elif compression_method == 'zip_bz2':
                compression_type = zipfile.ZIP_BZIP2
            else:
                compression_type = zipfile.ZIP_LZMA  

            with zipfile.ZipFile(zip_path, 'w', compression_type, compresslevel=9) as zipf:
                total_files = sum(len(files) for _, _, files in os.walk(folder_path))
                processed = 0

                for root, _, files in os.walk(folder_path):
                    for f in files:
                        file_path = os.path.join(root, f)
                        arcname = os.path.relpath(file_path, folder_path)
                        zipf.write(file_path, arcname)
                        processed += 1
                        if progress_callback:
                            progress_callback( (processed / total_files) * 100, f'Adding files: {processed}/{total_files}' )
                        print(f"  Added: {arcname} ({processed}/{total_files})")
                        sys.stdout.flush()

            print("ZIP file created successfully.")

            
            with open(zip_path, "rb") as f:
                data = f.read()

            print(f" ZIP size: {len(data)} bytes")

            
            password_hash = None
            if password:
                print(f"Applying password protection...")

                password_hash = hashlib.sha256(password.encode('utf-8')).hexdigest()[:16]

                salt = password_hash.encode('utf-8')[:16].ljust(16, b'\x00')

                key = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 100000, dklen=32)

                encrypted_data = bytearray()
                for i, byte in enumerate(data):
                    key_byte = key[i % len(key)]
                    encrypted_data.append(byte ^ key_byte)

                data = bytes(encrypted_data)
                print(f"Data encrypted with password (size: {len(data)} bytes)")

            print(f"No password protection applied" if not password else "")

            
            pixels_per_byte = 4
            folder_name = os.path.basename(folder_path)
            data_size = str(len(data))
            compression_info = compression_method
            password_info = password_hash if password_hash else "none"
            metadata = f"{folder_name}\x00{data_size}\x00{compression_info}\x00{password_info}\x00".encode()

            total_pixels_needed = math.ceil((len(data) + len(metadata)) / pixels_per_byte)
            size = math.ceil(math.sqrt(total_pixels_needed))

            
            max_size = 90000
            max_data_size = 500 * 1024 * 1024

            if len(data) > max_data_size:
                raise ValueError(f"Data size ({len(data)} bytes) exceeds maximum allowed size ({max_data_size} bytes). "
                               f"Consider using smaller files or splitting into multiple archives.")

            if size > max_size:
                raise ValueError(f"Image would be too large ({size}x{size} pixels). "
                               f"Maximum allowed size is {max_size}x{max_size} pixels. "
                               f"Data size: {len(data)} bytes")

            
            min_size = 100
            if size < min_size:
                size = min_size

            img = Image.new("RGBA", (size, size), color=(255, 255, 255, 255))
            rgba_bytes = bytearray(img.tobytes())

            print(f" Creating RGBA image of size {size}x{size} ({pixels_per_byte} bytes per pixel)...")

            print(f"Storing metadata: folder='{folder_name}', size={data_size}, compression={compression_info}")

            # Metadata in alpha channels
            for idx, b in enumerate(metadata):
                offset = idx * 4 + 3  # alpha
                if offset < len(rgba_bytes):
                    rgba_bytes[offset] = b + 1

            print(f"Metadata stored in {len(metadata)} alpha channels")

            # Data in RGBA channels
            data_start_idx = len(metadata)
            progress_step = max(1, len(data) // 100)

            for data_idx, byte in enumerate(data):
                # Calculate offset in rgba_bytes
                total_idx = data_start_idx + data_idx
                offset = total_idx
                if offset < len(rgba_bytes):
                    rgba_bytes[offset] = byte

                if data_idx % progress_step == 0:
                    percent = (data_idx / len(data)) * 100
                    if progress_callback:
                        progress_callback(percent)
                    print(f"\rEncoding data... {percent:.1f}%", end="")
                    sys.stdout.flush()

            print(f"\rData stored in {len(data)} RGBA channels.             ")
            img = Image.frombytes("RGBA", (size, size), rgba_bytes)
            img.save(output_png, optimize=True)
            print(f"Saved compressed image as '{output_png}'")

        finally:
            
            if os.path.exists(zip_path):
                os.remove(zip_path)

    except Exception as e:
        print(f"Fatal error in encode_folder_to_png: {e}")
        traceback.print_exc()
        raise
