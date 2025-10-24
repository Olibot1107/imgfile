from PIL import Image
Image.MAX_IMAGE_PIXELS = None  

import zipfile, io, os, sys, traceback, hashlib, getpass

def decode_png_to_folder(img_path, output_folder, password=None):
    """Extract files from a compressed PNG image with enhanced decoding"""
    try:
        if not os.path.exists(img_path):
            raise FileNotFoundError(f"Image not found: {img_path}")

        print(f"Loading image: {img_path}")
        img = Image.open(img_path)

        width, height = img.size
        mode = img.mode
        print(f"Image size: {width}x{height} pixels, mode: {mode}")

        
        if not os.path.exists(output_folder):
            os.makedirs(output_folder, exist_ok=True)

        
        print("Reconstructing data from pixels...")

        data_bytes = []
        metadata = ""

        total_pixels = width * height
        pixels_processed = 0
        channels_per_pixel = 4 if mode == 'RGBA' else 3

        
        print("Scanning for metadata pixels...")
        metadata_pixels_found = 0

        
        for x in range(min(width, 1000)):  
            if mode == 'RGBA':
                r, g, b, a = img.getpixel((x, 0))
            else:
                r, g, b = img.getpixel((x, 0))
                a = 255  

            
            if a != 255:
                
                original_byte = a - 1
                metadata += chr(original_byte)
                metadata_pixels_found += 1
                print(f"Found metadata pixel at ({x},0): {chr(original_byte)} (0x{original_byte:02x}) from alpha {a} (0x{a:02x})")
                if chr(original_byte) == '\x00' and metadata.count('\x00') >= 4:  
                    print(f"Found end of metadata after {metadata_pixels_found} pixels")
                    break

        print(f"\rMetadata extraction complete. Found {metadata_pixels_found} metadata pixels")
        print(f"Raw metadata: {repr(metadata)}")

        
        print("Scanning for data pixels...")
        pixels_processed = 0
        data_pixels_found = 0

        for y in range(height):
            for x in range(width):
                
                if y == 0:
                    continue

                if mode == 'RGBA':
                    r, g, b, a = img.getpixel((x, y))
                    
                    data_bytes.extend([r, g, b, a])
                    data_pixels_found += 1
                else:
                    r, g, b = img.getpixel((x, y))
                    
                    data_bytes.extend([r, g, b])
                    data_pixels_found += 1

                pixels_processed += 1
                if pixels_processed % (total_pixels // 100) == 0:
                    print(f"\rExtracting data... {pixels_processed / total_pixels * 100:.1f}%", end="")
                    sys.stdout.flush()

        print(f"\rPixel data reconstruction complete. Found {data_pixels_found} data pixels")
        print(f"Total data bytes extracted: {len(data_bytes)}")

        
        password_protected = False
        stored_password_hash = None

        try:
            if '\x00' in metadata and metadata.count('\x00') >= 4:
                
                parts = metadata.split('\x00', 4)
                if len(parts) >= 4:
                    folder_name = parts[0]
                    data_size_str = parts[1]
                    compression_method = parts[2]
                    stored_password_hash = parts[3]
                    expected_size = int(data_size_str)
                    password_protected = stored_password_hash != "none"
                    print(f"Original folder: {folder_name}")
                    print(f"Expected data size: {expected_size} bytes")
                    print(f"Compression method: {compression_method}")
                    print(f"Password protected: {password_protected}")
                    if password_protected:
                        print(f"Stored password hash: {stored_password_hash}")
                    print(f"Actual data size: {len(data_bytes)} bytes")
                else:
                    print("Incomplete enhanced metadata found, trying legacy format...")
                    if metadata.count('\x00') >= 2:
                        parts = metadata.split('\x00', 2)
                        folder_name = parts[0]
                        data_size_str = parts[1]
                        compression_method = "unknown (legacy)"
                        expected_size = int(data_size_str)
                        print(f"Legacy format detected")
                    else:
                        print("No valid metadata found, extracting all data...")
                        expected_size = None
                        compression_method = "unknown"
            elif '\x00' in metadata and metadata.count('\x00') >= 3:
                
                parts = metadata.split('\x00', 3)
                if len(parts) >= 3:
                    folder_name = parts[0]
                    data_size_str = parts[1]
                    compression_method = parts[2]
                    expected_size = int(data_size_str)
                    print(f"Original folder: {folder_name}")
                    print(f"Expected data size: {expected_size} bytes")
                    print(f"Compression method: {compression_method}")
                    print(f"Password protected: False")
                    print(f"Actual data size: {len(data_bytes)} bytes")
                else:
                    print("Incomplete enhanced metadata found, trying legacy format...")
                    if metadata.count('\x00') >= 2:
                        parts = metadata.split('\x00', 2)
                        folder_name = parts[0]
                        data_size_str = parts[1]
                        compression_method = "unknown (legacy)"
                        expected_size = int(data_size_str)
                        print(f"Legacy format detected")
                    else:
                        print("No valid metadata found, extracting all data...")
                        expected_size = None
                        compression_method = "unknown"
            elif '\x00' in metadata and metadata.count('\x00') >= 2:
                
                parts = metadata.split('\x00', 2)
                folder_name = parts[0]
                data_size_str = parts[1]
                compression_method = "unknown (legacy)"
                expected_size = int(data_size_str)
                print(f"Legacy metadata format detected")
            else:
                print("No metadata found, extracting all data...")
                expected_size = None
                compression_method = "unknown"
        except (ValueError, IndexError) as e:
            print(f"Error parsing metadata: {e}, extracting all data...")
            print(f"Metadata parts: {metadata.split(chr(0)) if chr(0) in metadata else 'No null bytes found'}")
            expected_size = None
            compression_method = "unknown"

        
        if password_protected:
            if not password:
                
                print(f"This image is password protected!")
                password = getpass.getpass("Enter password: ")

                if not password:
                    print(f"No password provided. Cannot decrypt protected image.")
                    print(f"Hint: The image contains garbled data without the correct password.")
                    return

            
            entered_password_hash = hashlib.sha256(password.encode('utf-8')).hexdigest()[:16]
            if entered_password_hash != stored_password_hash:
                print(f"Incorrect password! Access denied.")
                print(f"Hint: Without the correct password, the image contains only random/garbled data.")
                print(f"Expected hash: {stored_password_hash}")
                print(f"Entered hash: {entered_password_hash}")
                return

            print(f"Password verified! Decrypting data...")

            
            
            salt = stored_password_hash.encode('utf-8')[:16].ljust(16, b'\x00')
            key = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 100000, dklen=32)

            decrypted_data = bytearray()
            for i, byte in enumerate(data_bytes):
                key_byte = key[i % len(key)]
                decrypted_data.append(byte ^ key_byte)

            data_bytes = bytes(decrypted_data)
            print(f"Data decrypted successfully (size: {len(data_bytes)} bytes)")
        else:
            print(f"No password protection - proceeding with extraction")

        
        zip_bytes = io.BytesIO(bytes(data_bytes))
        print("Extracting files from ZIP data...")

        try:
            with zipfile.ZipFile(zip_bytes, 'r') as zipf:
                file_list = zipf.namelist()
                print(f"ZIP contains {len(file_list)} files")
                for idx, f in enumerate(file_list, start=1):
                    zipf.extract(f, output_folder)
                    print(f"  Extracted: {f} ({idx}/{len(file_list)})")

            print(f"Successfully decoded {img_path} -> {output_folder}/")

        except zipfile.BadZipFile as e:
            print(f"Error: The image does not contain a valid ZIP archive: {e}")
            print(f"ZIP data size: {len(data_bytes)} bytes")
            
            if len(data_bytes) > 100:
                print(f"First 100 bytes: {data_bytes[:100]}")
            raise
        except Exception as e:
            print(f"Unexpected error during ZIP extraction: {e}")
            traceback.print_exc()
            raise

    except Exception as e:
        print(f"Fatal error in decode_png_to_folder: {e}")
        traceback.print_exc()
        raise
