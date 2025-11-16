import os
import sys
import argparse
import subprocess
from tqdm import tqdm
from colorama import Fore, Back, Style, init
from encoder import encode_folder_to_png
from decoder import decode_png_to_folder, get_decode_info

def check_and_run_autorun(output_folder):
    if os.name == 'nt':
        script_name = 'autorun.bat'
    else:
        script_name = 'autorun.sh'

    script_path = os.path.join(output_folder, script_name)

    if os.path.exists(script_path):
        print(Fore.YELLOW + f"Autorun script found: {script_name}" + Style.RESET_ALL)
        try:
            with open(script_path, 'r', encoding='utf-8', errors='ignore') as f:
                script_content = f.read()
            print("Script content:")
            print(Fore.CYAN + "-" * 40 + Style.RESET_ALL)
            print(script_content)
            print(Fore.CYAN + "-" * 40 + Style.RESET_ALL)
            confirm = input("Are you sure you want to run this script? (type 'yes' to confirm): ").strip().lower()
            if confirm in ('y', 'yes'):
                print(Fore.YELLOW + "Running script..." + Style.RESET_ALL)
                try:
                    # Don't capture output so it prints to console in real-time
                    if os.name == 'nt':
                        result = subprocess.run(script_path, cwd=output_folder, shell=True, capture_output=False)
                    else:
                        os.chmod(script_path, 0o755)
                        result = subprocess.run(['sh', script_path], cwd=output_folder, capture_output=False)
                    if result.returncode == 0:
                        print(Fore.GREEN + "Script executed successfully." + Style.RESET_ALL)
                    else:
                        print(Fore.RED + f"Script failed with return code {result.returncode}." + Style.RESET_ALL)
                except Exception as e:
                    print(Fore.RED + f"Failed to run script: {e}" + Style.RESET_ALL)
            else:
                print("Script execution skipped.")
        except Exception as e:
            print(Fore.RED + f"Error reading autorun script: {e}" + Style.RESET_ALL)

def main():
    init()  # Initialize colorama for colored terminal output
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
            print(Fore.CYAN + "\nFile Compressor CLI" + Style.RESET_ALL)
            print(Fore.CYAN + "===================" + Style.RESET_ALL)
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
                print(Fore.RED + "Invalid choice. Please try again." + Style.RESET_ALL)

def compress_interactive():
    print(Fore.YELLOW + "\nCompress Folder to PNG" + Style.RESET_ALL)
    print(Fore.YELLOW + "======================" + Style.RESET_ALL)
    folder_path = input("Enter folder path to compress: ").strip()
    while not folder_path:
        print(Fore.RED + "Folder path cannot be empty." + Style.RESET_ALL)
        folder_path = input("Enter folder path to compress: ").strip()

    output_png = input("Enter output PNG file path (will add .png if no extension): ").strip()
    if not output_png:
        print(Fore.RED + "Output path cannot be empty." + Style.RESET_ALL)
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

    pbar = tqdm(total=100, unit='%', desc="Starting compression", colour='green')
    def progress_cb(p, msg):
        pbar.n = p
        pbar.desc = msg
        pbar.refresh()

    try:
        encode_folder_to_png(folder_path, output_png, method, progress_callback=progress_cb, enable_max_limit=enable_max_limit, password=password)
        pbar.close()
        print(Fore.GREEN + "\nCompression completed successfully!" + Style.RESET_ALL)
    except Exception as e:
        pbar.close()
        print(Fore.RED + f"\nCompression failed: {e}" + Style.RESET_ALL)

def compress_non_interactive(args):
    folder_path = args.folder
    output_png = args.output
    method = args.method
    enable_max_limit = args.limit
    password = args.password

    pbar = tqdm(total=100, unit='%', desc="Starting compression", colour='green')
    def progress_cb(p, msg):
        pbar.n = p
        pbar.desc = msg
        pbar.refresh()

    try:
        encode_folder_to_png(folder_path, output_png, method, progress_callback=progress_cb, enable_max_limit=enable_max_limit, password=password)
        pbar.close()
        print(Fore.GREEN + "\nCompression completed successfully!" + Style.RESET_ALL)
    except Exception as e:
        pbar.close()
        print(Fore.RED + f"\nCompression failed: {e}" + Style.RESET_ALL)

def extract_non_interactive(args):
    img_path = args.png
    output_folder = args.output_folder
    password = args.password

    folder_name, file_count, total_size, compression_method, password_info, _ = get_decode_info(img_path)

    if password_info == "encrypted" and not password:
        print(Fore.RED + "Password is required for extraction." + Style.RESET_ALL)
        return

    size_mb = total_size / (1024 * 1024)
    protection = "Password protected" if password_info == "encrypted" else "No password protection"
    print(Fore.BLUE + f"Folder: {folder_name}" + Style.RESET_ALL)
    print(f"Files: {file_count}")
    print(f"Total size: {size_mb:.2f} MB")
    print(f"Compression: {compression_method}")
    print(Fore.YELLOW + f"Protection: {protection}" + Style.RESET_ALL)

    pbar = tqdm(total=100, unit='%', desc="Starting extraction", colour='green')
    def progress_cb(p, msg):
        pbar.n = p
        pbar.desc = msg
        pbar.refresh()

    try:
        decode_png_to_folder(img_path, output_folder, progress_callback=progress_cb, password=password)
        pbar.close()
        print(Fore.GREEN + "\nExtraction completed successfully!" + Style.RESET_ALL)
        check_and_run_autorun(output_folder)
    except Exception as e:
        pbar.close()
        print(Fore.RED + f"\nExtraction failed: {e}" + Style.RESET_ALL)

def extract_interactive():
    print(Fore.MAGENTA + "\nExtract PNG to Folder" + Style.RESET_ALL)
    print(Fore.MAGENTA + "=====================" + Style.RESET_ALL)
    img_path = input("Enter PNG file path to extract: ").strip()
    output_folder = input("Enter output folder path: ").strip()

    folder_name, file_count, total_size, compression_method, password_info, _ = get_decode_info(img_path)

    size_mb = total_size / (1024 * 1024)
    protection = "Password protected" if password_info == "encrypted" else "No password protection"
    print(Fore.BLUE + f"\nFolder: {folder_name}" + Style.RESET_ALL)
    print(f"Files: {file_count}")
    print(f"Total size: {size_mb:.2f} MB")
    print(f"Compression: {compression_method}")
    print(Fore.YELLOW + f"Protection: {protection}" + Style.RESET_ALL)
    confirm = input("\nAre you sure you want to extract? (y/n): ").strip().lower()
    if confirm not in ('y', 'yes'):
        print(Fore.YELLOW + "Extraction cancelled." + Style.RESET_ALL)
        return

    if password_info == "encrypted":
        password = input("Enter password: ").strip()
        if not password:
            print(Fore.RED + "Password is required." + Style.RESET_ALL)
            return
    else:
        password = None

    pbar = tqdm(total=100, unit='%', desc="Starting extraction", colour='cyan')
    def progress_cb(p, msg):
        pbar.n = p
        pbar.desc = msg
        pbar.refresh()

    try:
        decode_png_to_folder(img_path, output_folder, progress_callback=progress_cb, password=password)
        pbar.close()
        print(Fore.GREEN + "\nExtraction completed successfully!" + Style.RESET_ALL)
        check_and_run_autorun(output_folder)
    except Exception as e:
        pbar.close()
        print(Fore.RED + f"\nExtraction failed: {e}" + Style.RESET_ALL)

if __name__ == '__main__':
    main()
