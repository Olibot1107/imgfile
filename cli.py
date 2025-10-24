import os
import sys
from encoder import encode_folder_to_png
from decoder import decode_png_to_folder

def main():
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

    password = input("Enter password (leave blank for no password): ").strip()
    password = password if password else None

    try:
        encode_folder_to_png(folder_path, output_png, method, password, progress_callback=print_progress)
        print("\nCompression completed successfully!")
    except Exception as e:
        print(f"\nCompression failed: {e}")

def extract_interactive():
    print("\nExtract PNG to Folder")
    print("=====================")
    img_path = input("Enter PNG file path to extract: ").strip()
    output_folder = input("Enter output folder path: ").strip()
    password = input("Enter password (leave blank if not protected): ").strip()
    password = password if password else None

    try:
        decode_png_to_folder(img_path, output_folder, password, progress_callback=print_progress)
        print("\nExtraction completed successfully!")
    except Exception as e:
        print(f"\nExtraction failed: {e}")

def print_progress(percent, message=''):
    print(f"{percent:.1f}%: {message}")

if __name__ == '__main__':
    main()
