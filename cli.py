import os
import sys
from tqdm import tqdm
from encoder import encode_folder_to_png, encode_file_to_png
from decoder import decode_png_to_folder, decode_png_to_file

def main():
    while True:
        print("\nFile Compressor CLI")
        print("===================")
        print("1. Compress folder to PNG")
        print("2. Compress file to PNG")
        print("3. Extract PNG to folder")
        print("4. Extract PNG to file")
        print("5. Exit")
        choice = input("Choose an option (1-5): ").strip()

        if choice == '1':
            compress_folder_interactive()
        elif choice == '2':
            compress_file_interactive()
        elif choice == '3':
            extract_folder_interactive()
        elif choice == '4':
            extract_file_interactive()
        elif choice == '5':
            break
        else:
            print("Invalid choice. Please try again.")

def compress_folder_interactive():
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

    pbar = tqdm(total=100, unit='%', desc="Starting compression")
    def progress_cb(p, msg):
        pbar.n = p
        pbar.desc = msg
        pbar.refresh()

    try:
        encode_folder_to_png(folder_path, output_png, method, progress_callback=progress_cb)
        pbar.close()
        print("\nCompression completed successfully!")
    except Exception as e:
        pbar.close()
        print(f"\nCompression failed: {e}")

def compress_file_interactive():
    print("\nCompress File to PNG")
    print("====================")
    file_path = input("Enter file path to compress: ").strip()
    while not file_path:
        print("File path cannot be empty.")
        file_path = input("Enter file path to compress: ").strip()

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

    pbar = tqdm(total=100, unit='%', desc="Starting compression")
    def progress_cb(p, msg):
        pbar.n = p
        pbar.desc = msg
        pbar.refresh()

    try:
        encode_file_to_png(file_path, output_png, method, progress_callback=progress_cb)
        pbar.close()
        print("\nCompression completed successfully!")
    except Exception as e:
        pbar.close()
        print(f"\nCompression failed: {e}")

def extract_folder_interactive():
    print("\nExtract PNG to Folder")
    print("=====================")
    img_path = input("Enter PNG file path to extract: ").strip()
    output_folder = input("Enter output folder path: ").strip()

    pbar = tqdm(total=100, unit='%', desc="Starting extraction")
    def progress_cb(p, msg):
        pbar.n = p
        pbar.desc = msg
        pbar.refresh()

    try:
        decode_png_to_folder(img_path, output_folder, progress_callback=progress_cb)
        pbar.close()
        print("\nExtraction completed successfully!")
    except Exception as e:
        pbar.close()
        print(f"\nExtraction failed: {e}")

def extract_file_interactive():
    print("\nExtract PNG to File")
    print("===================")
    img_path = input("Enter PNG file path to extract: ").strip()
    output_file = input("Enter output file path: ").strip()

    pbar = tqdm(total=100, unit='%', desc="Starting extraction")
    def progress_cb(p, msg):
        pbar.n = p
        pbar.desc = msg
        pbar.refresh()

    try:
        decode_png_to_file(img_path, output_file, progress_callback=progress_cb)
        pbar.close()
        print("\nExtraction completed successfully!")
    except Exception as e:
        pbar.close()
        print(f"\nExtraction failed: {e}")

if __name__ == '__main__':
    main()
