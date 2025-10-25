from PIL import Image
Image.MAX_IMAGE_PIXELS = None

import zipfile, io, os, sys, traceback

def decode_png_to_folder(img_path, output_folder, progress_callback=None):
    try:
        if not os.path.exists(img_path):
            raise FileNotFoundError(f"Image not found: {img_path}")

        print(f"Loading image: {img_path}")
        img = Image.open(img_path)

        width, height = img.size
        mode = img.mode
        channels_per_pixel = 4 if mode == 'RGBA' else 3
        print(f"Image size: {width}x{height} pixels, mode: {mode}, channels: {channels_per_pixel}")

        if not os.path.exists(output_folder):
            os.makedirs(output_folder, exist_ok=True)

        print("Collecting all channel values...")
        
        all_bytes = img.tobytes()

        
        if mode != 'RGBA':
            
            new_bytes = bytearray()
            for i in range(0, len(all_bytes), channels_per_pixel):
                new_bytes.extend(all_bytes[i:i+channels_per_pixel])
                new_bytes.append(255)  
            all_bytes = bytes(new_bytes)
            channels_per_pixel = 4

        total_pixels = width * height
        print("Scanning for metadata channels...")
        metadata = ""
        metadata_channels_found = 0
        i = 0
        while i < len(all_bytes) // 4:
            alpha_index = 4 * i + 3
            a = all_bytes[alpha_index]
            if a != 255:
                original_byte = a - 1
                if 0 <= original_byte <= 255:
                    metadata += chr(original_byte)
                    metadata_channels_found += 1
                    print(f"Found metadata at channel {alpha_index}: {chr(original_byte)} (0x{original_byte:02x}) from alpha {a} (0x{a:02x})")
                    if chr(original_byte) == '\x00' and metadata.count('\x00') >= 4:
                        print(f"Found end of metadata after {metadata_channels_found} channels")
                        break
                else:
                    print(f"Skipping invalid alpha value a={a}, original_byte={original_byte}")
            i += 1
            if i > 10000:
                break

        print(f"\rMetadata extraction complete. Found {metadata_channels_found} metadata channels")
        print(f"Raw metadata: {repr(metadata)}")


        try:
            if '\x00' in metadata and metadata.count('\x00') >= 4:

                parts = metadata.split('\x00', 4)
                if len(parts) >= 4:
                    folder_name = parts[0]
                    data_size_str = parts[1]
                    compression_method = parts[2]
                    
                    expected_size = int(data_size_str)
                    print(f"Original folder: {folder_name}")
                    print(f"Expected data size: {expected_size} bytes")
                    print(f"Compression method: {compression_method}")
                    print(f"Total bytes in image: {len(all_bytes)} bytes")
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
                    print(f"Total bytes in image: {len(all_bytes)} bytes")
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
            metadata_channels_found = 0

        start_byte = metadata_channels_found * 4
        if expected_size is not None:
            zip_data_length = int(expected_size)
        else:
            zip_data_length = len(all_bytes) - start_byte

        print(f"No password protection - proceeding with extraction")
        zip_data = all_bytes[start_byte : start_byte + zip_data_length]
            
        zip_bytes = io.BytesIO(zip_data)

        print("Extracting files from ZIP data...")

        try:
            with zipfile.ZipFile(zip_bytes, 'r') as zipf:
                file_list = zipf.namelist()
                print(f"ZIP contains {len(file_list)} files")
                for idx, f in enumerate(file_list, start=1):
                    zipf.extract(f, output_folder)
                    if progress_callback:
                        progress_callback(idx / len(file_list) * 100, f'Extracting files: {idx}/{len(file_list)}')
                    print(f"  Extracted: {f} ({idx}/{len(file_list)})")

            print(f"Successfully decoded {img_path} -> {output_folder}/")

        except zipfile.BadZipFile as e:
            print(f"Error: The image does not contain a valid ZIP archive: {e}")
            print(f"ZIP data size: {len(zip_data)} bytes")

            if len(zip_data) > 100:
                print(f"First 100 bytes: {zip_data[:100]}")
            raise
        except Exception as e:
            print(f"Unexpected error during ZIP extraction: {e}")
            traceback.print_exc()
            raise

    except Exception as e:
        print(f"Fatal error in decode_png_to_folder: {e}")
        traceback.print_exc()
        raise
