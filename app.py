"""
File Compressor Application

A GUI application for compressing folders into PNG images and extracting them back.
Uses Tkinter for the interface and custom encoder/decoder modules for compression.
"""

import os
import threading
from tkinter import filedialog, messagebox, ttk
import tkinter as tk

from encoder import encode_folder_to_png
from decoder import decode_png_to_folder


# Constants for UI styling
WINDOW_TITLE = "File Compressor"
WINDOW_SIZE = "440x380"
COMPRESS_WINDOW_SIZE = "400x350"
EXTRACT_WINDOW_SIZE = "350x200"
TITLE_FONT = ("Arial", 20, "bold")
LABEL_FONT = ("Arial", 12, "bold")
SMALL_FONT = ("Arial", 8, "italic")
BUTTON_FONT = ("Arial", 11)
FOOTER_FONT = ("Arial", 9)
TITLE_COLOR = "#2E8B57"
STATUS_COLOR = "#000080"
FOOTER_COLOR = "#666666"


def encode_action():
    """
    Handles the compression action: selects a folder, chooses compression settings,
    and initiates the encoding process in a background thread.
    """
    folder_path = filedialog.askdirectory(title="Select folder to compress")
    if not folder_path:
        return

    # Create compression settings window
    compress_window = tk.Toplevel(root)
    compress_window.title("Compression Settings")
    compress_window.geometry(COMPRESS_WINDOW_SIZE)
    compress_window.transient(root)
    compress_window.grab_set()

    # Compression method selection
    tk.Label(compress_window, text="Select Compression Method:", font=LABEL_FONT).pack(pady=10)

    compression_var = tk.StringVar(value="lzma")

    methods = [
        ("LZMA (Best compression)", "lzma"),
        ("BZIP2 (Good compression)", "bz2"),
        ("ZLIB (Fast compression)", "zlib"),
        ("ZIP-LZMA (Compatible)", "zip_lzma"),
        ("ZIP-BZIP2 (Compatible)", "zip_bz2"),
    ]
    for text, value in methods:
        ttk.Radiobutton(compress_window, text=text, variable=compression_var, value=value).pack(anchor="w", padx=20)

    # Password protection
    tk.Label(compress_window, text="Password Protection (Optional):", font=LABEL_FONT).pack(pady=10)

    password_var = tk.StringVar()
    password_confirm_var = tk.StringVar()

    tk.Label(compress_window, text="Password:").pack(anchor="w", padx=20)
    password_entry = tk.Entry(compress_window, textvariable=password_var, show="*", width=30)
    password_entry.pack(padx=20, pady=2)

    tk.Label(compress_window, text="Confirm Password:").pack(anchor="w", padx=20)
    password_confirm_entry = tk.Entry(compress_window, textvariable=password_confirm_var, show="*", width=30)
    password_confirm_entry.pack(padx=20, pady=2)

    tk.Label(compress_window, text="Leave blank for no password protection", font=SMALL_FONT).pack(pady=5)

    def proceed_compression():
        """Validates inputs and starts the compression process."""
        compression_method = compression_var.get()
        password = password_var.get()
        password_confirm = password_confirm_var.get()

        # Validation
        if password != password_confirm:
            messagebox.showerror("Error", "Passwords do not match!")
            return

        if password and len(password) < 4:
            messagebox.showerror("Error", "Password must be at least 4 characters long!")
            return

        # Output file selection
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

        # Background compression
        def encode_worker():
            try:
                def progress_cb(percent, message='Encoding'):
                    root.after(0, lambda: progress_bar.config(value=percent))
                    root.after(0, lambda: progress_label.config(text=f"{message}: {percent:.1f}%"))

                encode_folder_to_png(
                    folder_path,
                    output_path,
                    compression_method,
                    password if password else None,
                    progress_cb
                )
                protection_status = "with password protection" if password else "without password protection"
                root.after(0, lambda: messagebox.showinfo("Success",
                    f"Folder compressed to '{output_path}' using {compression_method.upper()} ({protection_status})!"
                ))
            except Exception as e:
                root.after(0, lambda: messagebox.showerror("Error", f"Compression failed: {str(e)}"))
            finally:
                root.after(0, lambda: progress_bar.config(value=0))
                root.after(0, lambda: progress_label.config(text="Idle"))

        threading.Thread(target=encode_worker, daemon=True).start()

    # Buttons
    tk.Button(compress_window, text="Compress", command=proceed_compression, width=15).pack(pady=15)
    tk.Button(compress_window, text="Cancel", command=compress_window.destroy, width=15).pack(pady=5)


def decode_action():
    """
    Handles the extraction action: selects a PNG file and output folder,
    prompts for password if needed, and initiates the decoding process in a background thread.
    """
    img_path = filedialog.askopenfilename(
        title="Select compressed PNG file",
        filetypes=[("PNG Images", "*.png")]
    )
    if not img_path:
        return

    output_folder = filedialog.askdirectory(title="Select output folder")
    if not output_folder:
        return

    # Create extraction settings window
    extract_window = tk.Toplevel(root)
    extract_window.title("Extraction Settings")
    extract_window.geometry(EXTRACT_WINDOW_SIZE)
    extract_window.transient(root)
    extract_window.grab_set()

    tk.Label(extract_window, text="Password (if required):", font=LABEL_FONT).pack(pady=10)

    password_var = tk.StringVar()

    tk.Label(extract_window, text="Password:").pack(anchor="w", padx=20)
    password_entry = tk.Entry(extract_window, textvariable=password_var, show="*", width=30)
    password_entry.pack(padx=20, pady=2)

    tk.Label(extract_window, text="Leave blank if no password protection", font=SMALL_FONT).pack(pady=5)

    def proceed_extraction():
        """Starts the extraction process."""
        password = password_var.get() if password_var.get() else None

        extract_window.destroy()

        # Background extraction
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

    # Buttons
    tk.Button(extract_window, text="Extract", command=proceed_extraction, width=15).pack(pady=15)
    tk.Button(extract_window, text="Cancel", command=extract_window.destroy, width=15).pack(pady=5)


# Main application setup
root = tk.Tk()
root.title(WINDOW_TITLE)
root.geometry(WINDOW_SIZE)
root.resizable(False, False)

# Main frame
main_frame = ttk.Frame(root)
main_frame.pack(padx=15, pady=15, fill="both", expand=True)

# Title
title_label = tk.Label(main_frame, text="File Compressor", font=TITLE_FONT, fg=TITLE_COLOR)
title_label.pack(pady=(0, 15))

# Buttons frame
buttons_frame = ttk.Frame(main_frame)
buttons_frame.pack()

# Button styling
style = ttk.Style()
style.configure("TButton", font=BUTTON_FONT, padding=6)

compress_btn = ttk.Button(buttons_frame, text="Compress Folder to PNG", command=encode_action, width=40)
compress_btn.pack(pady=(0, 8))

extract_btn = ttk.Button(buttons_frame, text="Extract PNG to Folder", command=decode_action, width=40)
extract_btn.pack(pady=(8, 10))

# Progress section
progress_frame = ttk.Frame(main_frame)
progress_frame.pack(pady=(10, 0))

progress_bar = ttk.Progressbar(progress_frame, orient="horizontal", length=380, mode="determinate")
progress_bar.pack(pady=5)

progress_label = ttk.Label(progress_frame, text="Idle", font=BUTTON_FONT, foreground=STATUS_COLOR)
progress_label.pack(pady=5)

# Footer
footer_label = ttk.Label(main_frame, text="Made by Olibot13 and chatgpt", font=FOOTER_FONT, foreground=FOOTER_COLOR)
footer_label.pack(side="bottom", pady=(15, 0))

root.mainloop()
