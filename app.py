import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import os, threading
from encoder import encode_folder_to_png
from decoder import decode_png_to_folder

def encode_action():
    folder_path = filedialog.askdirectory(title="Select folder to compress")
    if not folder_path:
        return

    
    compress_window = tk.Toplevel(root)
    compress_window.title("Compression Settings")
    compress_window.geometry("400x350")
    compress_window.transient(root)
    compress_window.grab_set()

    tk.Label(compress_window, text="Select Compression Method:", font=("Arial", 12, "bold")).pack(pady=10)

    compression_var = tk.StringVar(value="lzma")

    ttk.Radiobutton(compress_window, text="LZMA (Best compression)", variable=compression_var, value="lzma").pack(anchor="w", padx=20)
    ttk.Radiobutton(compress_window, text="BZIP2 (Good compression)", variable=compression_var, value="bz2").pack(anchor="w", padx=20)
    ttk.Radiobutton(compress_window, text="ZLIB (Fast compression)", variable=compression_var, value="zlib").pack(anchor="w", padx=20)
    ttk.Radiobutton(compress_window, text="ZIP-LZMA (Compatible)", variable=compression_var, value="zip_lzma").pack(anchor="w", padx=20)
    ttk.Radiobutton(compress_window, text="ZIP-BZIP2 (Compatible)", variable=compression_var, value="zip_bz2").pack(anchor="w", padx=20)

    
    tk.Label(compress_window, text="Password Protection (Optional):", font=("Arial", 12, "bold")).pack(pady=10)

    password_var = tk.StringVar()
    password_confirm_var = tk.StringVar()

    tk.Label(compress_window, text="Password:").pack(anchor="w", padx=20)
    password_entry = tk.Entry(compress_window, textvariable=password_var, show="*", width=30)
    password_entry.pack(padx=20, pady=2)

    tk.Label(compress_window, text="Confirm Password:").pack(anchor="w", padx=20)
    password_confirm_entry = tk.Entry(compress_window, textvariable=password_confirm_var, show="*", width=30)
    password_confirm_entry.pack(padx=20, pady=2)

    tk.Label(compress_window, text="Leave blank for no password protection", font=("Arial", 8, "italic")).pack(pady=5)

    def proceed_compression():
        compression_method = compression_var.get()
        password = password_var.get()
        password_confirm = password_confirm_var.get()

        
        if password != password_confirm:
            messagebox.showerror("Error", "Passwords do not match!")
            return

        if password and len(password) < 4:
            messagebox.showerror("Error", "Password must be at least 4 characters long!")
            return

        output_name = os.path.basename(folder_path) + ".png"
        output_path = filedialog.asksaveasfilename(
            defaultextension=".png",
            filetypes=[("PNG Images", "*.png")],
            initialfile=output_name
        )

        if not output_path:
            compress_window.destroy()
            return

        compress_window.destroy()

        def encode_worker():
            try:
                encode_folder_to_png(folder_path, output_path, compression_method, password if password else None)
                protection_status = "with password protection" if password else "without password protection"
                messagebox.showinfo("Success", f"Folder compressed to '{output_path}' using {compression_method.upper()} ({protection_status})!")
            except Exception as e:
                messagebox.showerror("Error", f"Compression failed: {str(e)}")

        threading.Thread(target=encode_worker, daemon=True).start()

    tk.Button(compress_window, text="Compress", command=proceed_compression, width=15).pack(pady=15)
    tk.Button(compress_window, text="Cancel", command=compress_window.destroy, width=15).pack(pady=5)

def decode_action():
    img_path = filedialog.askopenfilename(
        title="Select compressed PNG file",
        filetypes=[("PNG Images", "*.png")]
    )
    if not img_path:
        return

    output_folder = filedialog.askdirectory(title="Select output folder")
    if not output_folder:
        return

    
    extract_window = tk.Toplevel(root)
    extract_window.title("Extraction Settings")
    extract_window.geometry("350x200")
    extract_window.transient(root)
    extract_window.grab_set()

    tk.Label(extract_window, text="Password (if required):", font=("Arial", 12, "bold")).pack(pady=10)

    password_var = tk.StringVar()

    tk.Label(extract_window, text="Password:").pack(anchor="w", padx=20)
    password_entry = tk.Entry(extract_window, textvariable=password_var, show="*", width=30)
    password_entry.pack(padx=20, pady=2)

    tk.Label(extract_window, text="Leave blank if no password protection", font=("Arial", 8, "italic")).pack(pady=5)

    def proceed_extraction():
        password = password_var.get() if password_var.get() else None

        extract_window.destroy()

        def decode_worker():
            try:
                decode_png_to_folder(img_path, output_folder, password)
                messagebox.showinfo("Success", f"Files extracted to '{output_folder}'!")
            except Exception as e:
                messagebox.showerror("Error", f"Extraction failed: {str(e)}")

        threading.Thread(target=decode_worker, daemon=True).start()

    tk.Button(extract_window, text="Extract", command=proceed_extraction, width=15).pack(pady=15)
    tk.Button(extract_window, text="Cancel", command=extract_window.destroy, width=15).pack(pady=5)


root = tk.Tk()
root.title("File Compressor")
root.geometry("400x250")

tk.Label(root, text="File Compressor", font=("Arial", 16, "bold")).pack(pady=10)

tk.Button(root, text="Compress Folder to PNG", command=encode_action, width=35, height=2).pack(pady=5)
tk.Button(root, text="Extract PNG to Folder", command=decode_action, width=35, height=2).pack(pady=5)

tk.Label(root, text="Made by Olibot13 and chatgpt", font=("Arial", 10)).pack(side="bottom", pady=10)

root.mainloop()
