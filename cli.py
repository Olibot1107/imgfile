import os
import sys
import argparse
from tqdm import tqdm
from encoder import encode_folder_to_png
from decoder import decode_png_to_folder, get_decode_info

def main():
    parser = argparse.ArgumentParser(description="File Compressor CLI")
    subparsers = parser.add_subparsers(dest='command')

    compress_parser = subparsers.add_parser('compress', help='Compress folder to PNG')
    compress_parser.add_argument('folder', help='Folder to compress')
    compress_parser.add_argument('output', help='Output PNG file')
    compress_parser.add_argument('--method', default='lzma', choices=['lzma', 'bz2', 'zlib', 'zip_lzma', 'zip_bz2'], help='Compression method')
    compress_parser.add_argument('--limit', default=True, type=bool, help='Enable max file limit')
    compress_parser.add_argument('--password', help='Password for encryption')

    extract_parser = subparsers.add_parser('extract', help='Extract PNG to folder')
    extract_parser.add_argument('png', help='PNG file to extract')
    extract_parser.add_argument('output_folder', help='Output folder')
    extract_parser.add_argument('--password', help='Password for decryption')

    args = parser.parse_args()

    if args.command == 'compress':
        compress_non_interactive(args)
    elif args.command == 'extract':
        extract_non_interactive(args)
    else:
        while True:
            print("\nFile Compressor CLI")
            print("===================")
            print("1. Compress folder to PNG")
            print("2. Extract PNG to folder")
            print("3. Exit")
            choice = input("Choose an option (1-3): ").strip()

            if choice == '1':
                compress_interactive()
            elif choice == '2':
                extract_interactive()
            elif choice == '3':
                break
            else:
                print("Invalid choice. Please try again.")

def compress_interactive():
    print("\nCompress Folder to PNG")
    print("======================")
    folder_path = input("Enter folder path to compress: ").strip()
    while not folder_path:
        print("Folder path cannot be empty.")
        folder_path = input("Enter folder path to compress: ").strip()

    output_png = input("Enter output PNG file path (will add .png if no extension): ").strip()
    if not output_png:
        print("Output path cannot be empty.")
        return
    if not output_png.lower().endswith('.png'):
        output_png += '.png'

    print("\nCompression Methods:")
    methods = ['lzma', 'bz2', 'zlib', 'zip_lzma', 'zip_bz2']
    for i, m in enumerate(methods, 1):
        print(f"{i}. {m.upper()}")
    method_choice = input("Choose compression method (1-5, default 1): ").strip()
    method = methods[int(method_choice) - 1] if method_choice.isdigit() and 1 <= int(method_choice) <= 5 else 'lzma'

    enable_limit = input("Enable max file limit? (y/n, default y): ").strip().lower()
    enable_max_limit = enable_limit in ('y', 'yes', '') or enable_limit == ''

    password = input("Enter password (optional, leave blank for none): ").strip()
    if not password:
        password = None

    pbar = tqdm(total=100, unit='%', desc="Starting compression")
    def progress_cb(p, msg):
        pbar.n = p
        pbar.desc = msg
        pbar.refresh()

    try:
        encode_folder_to_png(folder_path, output_png, method, progress_callback=progress_cb, enable_max_limit=enable_max_limit, password=password)
        pbar.close()
        print("\nCompression completed successfully!")
    except Exception as e:
        pbar.close()
        print(f"\nCompression failed: {e}")

def compress_non_interactive(args):
    folder_path = args.folder
    output_png = args.output
    method = args.method
    enable_max_limit = args.limit
    password = args.password

    pbar = tqdm(total=100, unit='%', desc="Starting compression")
    def progress_cb(p, msg):
        pbar.n = p
        pbar.desc = msg
        pbar.refresh()

    try:
        encode_folder_to_png(folder_path, output_png, method, progress_callback=progress_cb, enable_max_limit=enable_max_limit, password=password)
        pbar.close()
        print("\nCompression completed successfully!")
    except Exception as e:
        pbar.close()
        print(f"\nCompression failed: {e}")

def extract_non_interactive(args):
    img_path = args.png
    output_folder = args.output_folder
    password = args.password

    folder_name, file_count, total_size, compression_method, password_info = get_decode_info(img_path)

    if password_info == "encrypted" and not password:
        print("Password is required for extraction.")
        return

    size_mb = total_size / (1024 * 1024)
    protection = "Password protected" if password_info == "encrypted" else "No password protection"
    print(f"Folder: {folder_name}")
    print(f"Files: {file_count}")
    print(f"Total size: {size_mb:.2f} MB")
    print(f"Compression: {compression_method}")
    print(f"Protection: {protection}")

    pbar = tqdm(total=100, unit='%', desc="Starting extraction")
    def progress_cb(p, msg):
        pbar.n = p
        pbar.desc = msg
        pbar.refresh()

    try:
        decode_png_to_folder(img_path, output_folder, progress_callback=progress_cb, password=password)
        pbar.close()
        print("\nExtraction completed successfully!")
    except Exception as e:
        pbar.close()
        print(f"\nExtraction failed: {e}")

def extract_interactive():
    print("\nExtract PNG to Folder")
    print("=====================")
    img_path = input("Enter PNG file path to extract: ").strip()
    output_folder = input("Enter output folder path: ").strip()

    folder_name, file_count, total_size, compression_method, password_info = get_decode_info(img_path)

    size_mb = total_size / (1024 * 1024)
    protection = "Password protected" if password_info == "encrypted" else "No password protection"
    print(f"\nFolder: {folder_name}")
    print(f"Files: {file_count}")
    print(f"Total size: {size_mb:.2f} MB")
    print(f"Compression: {compression_method}")
    print(f"Protection: {protection}")
    confirm = input("\nAre you sure you want to extract? (y/n): ").strip().lower()
    if confirm not in ('y', 'yes'):
        print("Extraction cancelled.")
        return

    if password_info == "encrypted":
        password = input("Enter password: ").strip()
        if not password:
            print("Password is required.")
            return
    else:
        password = None

    pbar = tqdm(total=100, unit='%', desc="Starting extraction")
    def progress_cb(p, msg):
        pbar.n = p
        pbar.desc = msg
        pbar.refresh()

    try:
        decode_png_to_folder(img_path, output_folder, progress_callback=progress_cb, password=password)
        pbar.close()
        print("\nExtraction completed successfully!")
    except Exception as e:
        pbar.close()
        print(f"\nExtraction failed: {e}")

if __name__ == '__main__':
    main()
