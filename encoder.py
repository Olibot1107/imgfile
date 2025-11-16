from PIL import Image
import os, zipfile, math, sys, traceback, lzma, bz2, hashlib, secrets, io
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64
from colorama import Fore, Style

max_data_size = 500 * 1024 * 1024
max_size = 90000

def encode_folder_to_png(folder_path, output_png, compression_method='lzma', progress_callback=None, enable_max_limit=True, password=None, log_callback=None):
    if not os.path.exists('tmp'):
        os.makedirs('tmp')

    try:
        if not os.path.exists(folder_path):
            raise FileNotFoundError(f"Folder not found: {folder_path}")

        if not os.path.isdir(folder_path):
            raise NotADirectoryError(f"Path is not a directory: {folder_path}")


        msg = f"Creating compressed archive from '{folder_path}' using {compression_method}..."
        if log_callback:
            log_callback(msg)
        else:
            print(Fore.CYAN + msg + Style.RESET_ALL)

        zip_bytes = io.BytesIO()

        if compression_method == 'lzma':
            compression_type = zipfile.ZIP_LZMA
            compresslevel = 1
        elif compression_method == 'bz2':
            compression_type = zipfile.ZIP_BZIP2
            compresslevel = 1
        elif compression_method == 'zlib':
            compression_type = zipfile.ZIP_DEFLATED
            compresslevel = 1
        elif compression_method == 'zip_lzma':
            compression_type = zipfile.ZIP_LZMA
            compresslevel = 1
        elif compression_method == 'zip_bz2':
            compression_type = zipfile.ZIP_BZIP2
            compresslevel = 1
        else:
            compression_type = zipfile.ZIP_LZMA
            compresslevel = 1

        with zipfile.ZipFile(zip_bytes, 'w', compression_type, compresslevel=compresslevel) as zipf:
            total_files = sum(len(files) for _, _, files in os.walk(folder_path))
            processed = 0

            for root, _, files in os.walk(folder_path):
                for f in files:
                    file_path = os.path.join(root, f)
                    arcname = os.path.relpath(file_path, folder_path)
                    zipf.write(file_path, arcname)
                    msg = f"Added: {arcname}"
                    if log_callback:
                        log_callback(msg)
                    else:
                        print(Fore.CYAN + msg + Style.RESET_ALL)
                    processed += 1
                    if progress_callback and processed % max(1, total_files // 100) == 0:
                        progress_callback((processed / total_files) * 100, f'Adding files: {processed}/{total_files}')

        msg = "ZIP file created successfully."
        if log_callback:
            log_callback(msg)
        else:
            print(Fore.GREEN + msg + Style.RESET_ALL)

        data = zip_bytes.getvalue()

        msg = f"ZIP size: {len(data)} bytes"
        if log_callback:
            log_callback(msg)
        else:
            print(Fore.BLUE + msg + Style.RESET_ALL)

        if password:
            salt = os.urandom(16)
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt,
                iterations=100000,
            )
            key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
            fernet = Fernet(key)
            data = salt + fernet.encrypt(data)
            password_info = "encrypted"
            msg = "Password protection applied"
            if log_callback:
                log_callback(msg)
            else:
                print(Fore.YELLOW + msg + Style.RESET_ALL)
        else:
            password_info = "none"
            msg = "No password protection applied"
            if log_callback:
                log_callback(msg)
            else:
                print(Fore.GREEN + msg + Style.RESET_ALL)

        pixels_per_byte = 4
        folder_name = os.path.basename(folder_path)
        data_size = str(len(data))
        compression_info = compression_method
        metadata = f"{folder_name}\x00{data_size}\x00{compression_info}\x00{password_info}\x00".encode()

        meta_pixels = len(metadata)
        data_pixels = math.ceil(len(data) / pixels_per_byte)
        total_pixels_needed = meta_pixels + data_pixels
        size = math.ceil(math.sqrt(total_pixels_needed))

        if enable_max_limit:
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

        rgba_length = size * size * 4
        rgba_bytes = bytearray(b'\xFF' * rgba_length)

        msg = f"Creating RGBA image of size {size}x{size} ({pixels_per_byte} bytes per pixel)..."
        if log_callback:
            log_callback(msg)
        else:
            print(Fore.CYAN + msg + Style.RESET_ALL)

        msg = f"Storing metadata: folder='{folder_name}', size={data_size}, compression={compression_info}"
        if log_callback:
            log_callback(msg)
        else:
            print(Fore.CYAN + msg + Style.RESET_ALL)

        for idx, b in enumerate(metadata):
            offset = idx * 4 + 3
            if offset < len(rgba_bytes):
                rgba_bytes[offset] = b + 1

        msg = f"Metadata stored in {len(metadata)} alpha channels"
        if log_callback:
            log_callback(msg)
        else:
            print(Fore.GREEN + msg + Style.RESET_ALL)

        data_start_idx = len(metadata) * pixels_per_byte
        data_end_idx = data_start_idx + len(data)
        if data_end_idx <= len(rgba_bytes):
            # Store data in chunks to show progress and potentially speed up
            chunk_size = 1024 * 1024  # 1MB chunks
            total_data = len(data)
            for i in range(0, total_data, chunk_size):
                end_i = min(i + chunk_size, total_data)
                rgba_bytes[data_start_idx + i : data_start_idx + end_i] = data[i:end_i]
                if progress_callback:
                    progress_val = 50 + (i / total_data) * 50  # From 50 to 100 during data storage
                    progress_callback(progress_val, f'Storing data: {i // chunk_size + 1}/{ (total_data + chunk_size - 1) // chunk_size } chunks')
            if progress_callback:
                progress_callback(100, 'Complete')
        else:
            raise ValueError(f"Data ({len(data)} bytes) too large for image ({len(rgba_bytes)} bytes)")

        msg = f"Data stored in {len(data)} RGBA channels."
        if log_callback:
            log_callback(msg)
        else:
            print(Fore.GREEN + msg + Style.RESET_ALL)
        img = Image.frombytes("RGBA", (size, size), rgba_bytes)
        img.save(output_png, optimize=True)
        msg = f"Saved compressed image as '{output_png}'"
        if log_callback:
            log_callback(msg)
        else:
            print(Fore.GREEN + msg + Style.RESET_ALL)

    except Exception as e:
        print(Fore.RED + f"Fatal error in encode_folder_to_png: {e}" + Style.RESET_ALL)
        traceback.print_exc()
        raise
