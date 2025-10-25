from PIL import Image
Image.MAX_IMAGE_PIXELS = None

import zipfile, io, os, sys, traceback
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64

def decode_png_to_folder(img_path, output_folder, progress_callback=None, password=None):
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
                if len(parts) >= 5:
                    folder_name = parts[0]
                    data_size_str = parts[1]
                    compression_method = parts[2]
                    password_info = parts[3]
                    expected_size = int(data_size_str)
                    print(f"Original folder: {folder_name}")
                    print(f"Expected data size: {expected_size} bytes")
                    print(f"Compression method: {compression_method}")
                    print(f"Total bytes in image: {len(all_bytes)} bytes")
                elif len(parts) >= 4:
                    folder_name = parts[0]
                    data_size_str = parts[1]
                    compression_method = parts[2]
                    password_info = "none"
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
                        password_info = "none"
                        expected_size = int(data_size_str)
                        print(f"Legacy format detected")
                    else:
                        print("No valid metadata found, extracting all data...")
                        expected_size = None
                        compression_method = "unknown"
                        password_info = "none"
            elif '\x00' in metadata and metadata.count('\x00') >= 3:

                parts = metadata.split('\x00', 3)
                if len(parts) >= 4:
                    folder_name = parts[0]
                    data_size_str = parts[1]
                    compression_method = parts[2]
                    password_info = parts[3]
                    expected_size = int(data_size_str)
                    print(f"Original folder: {folder_name}")
                    print(f"Expected data size: {expected_size} bytes")
                    print(f"Compression method: {compression_method}")
                    print(f"Total bytes in image: {len(all_bytes)} bytes")
                elif len(parts) >= 3:
                    folder_name = parts[0]
                    data_size_str = parts[1]
                    compression_method = parts[2]
                    password_info = "none"
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
                        password_info = "none"
                        expected_size = int(data_size_str)
                        print(f"Legacy format detected")
                    else:
                        print("No valid metadata found, extracting all data...")
                        expected_size = None
                        compression_method = "unknown"
                        password_info = "none"
            elif '\x00' in metadata and metadata.count('\x00') >= 2:

                parts = metadata.split('\x00', 2)
                folder_name = parts[0]
                data_size_str = parts[1]
                compression_method = "unknown (legacy)"
                password_info = "none"
                expected_size = int(data_size_str)
                print(f"Legacy metadata format detected")
            else:
                print("No metadata found, extracting all data...")
                expected_size = None
                compression_method = "unknown"
                password_info = "none"
        except (ValueError, IndexError) as e:
            print(f"Error parsing metadata: {e}, extracting all data...")
            print(f"Metadata parts: {metadata.split(chr(0)) if chr(0) in metadata else 'No null bytes found'}")
            expected_size = None
            compression_method = "unknown"
            password_info = "none"
            metadata_channels_found = 0

        start_byte = metadata_channels_found * 4
        if expected_size is not None:
            zip_data_length = int(expected_size)
        else:
            zip_data_length = len(all_bytes) - start_byte

        zip_data = all_bytes[start_byte : start_byte + zip_data_length]

        if password_info == "encrypted":
            if not password:
                raise ValueError("Password required for encrypted archive")
            salt = zip_data[:16]
            encrypted_data = zip_data[16:]
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt,
                iterations=100000,
            )
            key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
            fernet = Fernet(key)
            zip_data = fernet.decrypt(encrypted_data)
            print("Password protection decrypted")
        else:
            print("No password protection - proceeding with extraction")

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


def get_decode_info(img_path):
    """
    Get information about the encoded PNG without extracting.
    Returns: folder_name, file_count, total_size, compression_method
    """
    try:
        if not os.path.exists(img_path):
            raise FileNotFoundError(f"Image not found: {img_path}")

        print(f"Loading image for info: {img_path}")
        img = Image.open(img_path)

        width, height = img.size
        mode = img.mode
        channels_per_pixel = 4 if mode == 'RGBA' else 3

        all_bytes = img.tobytes()

        if mode != 'RGBA':
            new_bytes = bytearray()
            for i in range(0, len(all_bytes), channels_per_pixel):
                new_bytes.extend(all_bytes[i:i+channels_per_pixel])
                new_bytes.append(255)
            all_bytes = bytes(new_bytes)
            channels_per_pixel = 4

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
                    if chr(original_byte) == '\x00' and metadata.count('\x00') >= 4:
                        break
            i += 1
            if i > 10000:
                break

        parts = metadata.split('\x00', 4)
        if len(parts) >= 5:
            folder_name = parts[0]
            data_size_str = parts[1]
            compression_method = parts[2]
            password_info = parts[3]
            expected_size = int(data_size_str)
        else:
            folder_name = "Unknown"
            compression_method = "Unknown"
            password_info = "none"
            expected_size = len(all_bytes) - metadata_channels_found * 4

        start_byte = metadata_channels_found * 4
        zip_data = all_bytes[start_byte : start_byte + expected_size]
        zip_bytes = io.BytesIO(zip_data)

        file_count = 0
        total_size = 0
        try:
            with zipfile.ZipFile(zip_bytes, 'r') as zipf:
                file_list = zipf.namelist()
                file_count = len(file_list)
                for f in file_list:
                    total_size += zipf.getinfo(f).file_size
        except zipfile.BadZipFile:
            file_count = 0
            total_size = 0

        return folder_name, file_count, total_size, compression_method, password_info

    except Exception as e:
        print(f"Error getting decode info: {e}")
        return "Unknown", 0, 0, "Unknown"
