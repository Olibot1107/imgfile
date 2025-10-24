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
                def progress_cb(percent, message='Encoding'):
                    root.after(0, lambda: progress_bar.config(value=percent))
                    root.after(0, lambda: progress_label.config(text=f"{message}: {percent:.1f}%"))
                encode_folder_to_png(folder_path, output_path, compression_method, password if password else None, progress_cb)
                protection_status = "with password protection" if password else "without password protection"
                root.after(0, lambda: messagebox.showinfo("Success", f"Folder compressed to '{output_path}' using {compression_method.upper()} ({protection_status})!"))
            except Exception as e:
                root.after(0, lambda: messagebox.showerror("Error", f"Compression failed: {str(e)}"))
            finally:
                root.after(0, lambda: progress_bar.config(value=0))
                root.after(0, lambda: progress_label.config(text="Idle"))

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
                def progress_cb(percent, message='Extracting'):
                    root.after(0, lambda: progress_bar.config(value=percent))
                    root.after(0, lambda: progress_label.config(text=f"{message}: {percent:.1f}%"))
                decode_png_to_folder(img_path, output_folder, password, progress_cb)
                root.after(0, lambda: messagebox.showinfo("Success", f"Files extracted to '{output_folder}'!"))
            except Exception as e:
                root.after(0, lambda: messagebox.showerror("Error", f"Extraction failed: {str(e)}"))
            finally:
                root.after(0, lambda: progress_bar.config(value=0))
                root.after(0, lambda: progress_label.config(text="Idle"))

        threading.Thread(target=decode_worker, daemon=True).start()

    tk.Button(extract_window, text="Extract", command=proceed_extraction, width=15).pack(pady=15)
    tk.Button(extract_window, text="Cancel", command=extract_window.destroy, width=15).pack(pady=5)


root = tk.Tk()
root.title("File Compressor")
root.geometry("440x380")
root.resizable(False, False)

# Main frame with padding
main_frame = ttk.Frame(root)
main_frame.pack(padx=15, pady=15, fill="both", expand=True)

# Title label with better styling
title_label = tk.Label(main_frame, text="File Compressor", font=("Arial", 20, "bold"), fg="#2E8B57")
title_label.pack(pady=(0, 15))

# Buttons frame
buttons_frame = ttk.Frame(main_frame)
buttons_frame.pack()

# Style buttons
style = ttk.Style()
style.configure("TButton", font=("Arial", 11), padding=6)

compress_btn = ttk.Button(buttons_frame, text="Compress Folder to PNG", command=encode_action, width=40)
compress_btn.pack(pady=(0, 8))

extract_btn = ttk.Button(buttons_frame, text="Extract PNG to Folder", command=decode_action, width=40)
extract_btn.pack(pady=(8, 10))

# Progress frame
progress_frame = ttk.Frame(main_frame)
progress_frame.pack(pady=(10, 0))

progress_bar = ttk.Progressbar(progress_frame, orient="horizontal", length=380, mode="determinate")
progress_bar.pack(pady=5)

progress_label = ttk.Label(progress_frame, text="Idle", font=("Arial", 11), foreground="#000080")
progress_label.pack(pady=5)

# Footer label
footer_label = ttk.Label(main_frame, text="Made by Olibot13 and chatgpt", font=("Arial", 9), foreground="#666666")
footer_label.pack(side="bottom", pady=(15, 0))

root.mainloop()
