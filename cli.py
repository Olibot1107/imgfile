import os
import sys
from tqdm import tqdm
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

def extract_interactive():
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

if __name__ == '__main__':
    main()
