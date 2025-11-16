import os
import threading
import time
import tkinter as tk
from tkinter import filedialog, messagebox, ttk, simpledialog, scrolledtext

from tqdm import tqdm

from encoder import encode_folder_to_png
from decoder import decode_png_to_folder, get_decode_info

WINDOW_TITLE = "File Compressor"
WINDOW_SIZE = "500x650"
COMPRESS_WINDOW_SIZE = "450x500"
EXTRACT_WINDOW_SIZE = "400x250"

TITLE_FONT = ("Helvetica", 24, "bold")
LABEL_FONT = ("Helvetica", 14, "bold")
SMALL_FONT = ("Helvetica", 10, "italic")
BUTTON_FONT = ("Helvetica", 12)
FOOTER_FONT = ("Helvetica", 10)

BG_COLOR = "#1E1E1E"  # Dark gray background
FRAME_BG = "#2D2D2D"  # Slightly lighter gray for frames
TITLE_COLOR = "#FFD700"  # Gold
STATUS_COLOR = "#87CEEB"  # Sky blue
FOOTER_COLOR = "#B0B0B0"  # Light gray
BUTTON_BG = "#00BFFF"
BUTTON_FG = "#000000"

COMPRESSION_METHODS = [
    ("LZMA (Best compression)", "lzma"),
    ("BZIP2 (Good compression)", "bz2"),
    ("ZLIB (Fast compression)", "zlib"),
    ("ZIP-LZMA (Compatible)", "zip_lzma"),
    ("ZIP-BZIP2 (Compatible)", "zip_bz2"),
]


def encode_action():
    """
    Handle the compression action: select folder, choose settings,
    and initiate encoding in background thread.
    """
    root.after(0, lambda: log_text.delete('1.0', tk.END))  # Clear log

    folder_path = filedialog.askdirectory(title="Select folder to compress")
    if not folder_path:
        return

    compress_window = tk.Toplevel(root)
    compress_window.title("Compression Settings")
    compress_window.geometry(COMPRESS_WINDOW_SIZE)
    compress_window.configure(bg=FRAME_BG)
    compress_window.transient(root)
    compress_window.grab_set()

    tk.Label(compress_window, text="Select Compression Method:",
             font=LABEL_FONT, bg=FRAME_BG, fg=TITLE_COLOR).pack(pady=10)

    compression_var = tk.StringVar(value="lzma")

    for text, value in COMPRESSION_METHODS:
        ttk.Radiobutton(
            compress_window,
            text=text,
            variable=compression_var,
            value=value
        ).pack(anchor="w", padx=20)

    enable_limit_var = tk.BooleanVar(value=True)
    ttk.Checkbutton(
        compress_window,
        text="Enable max file limit (500MB, 90000px)",
        variable=enable_limit_var
    ).pack(anchor="w", padx=20, pady=10)

    tk.Label(compress_window, text="Password (optional):", font=LABEL_FONT, bg=FRAME_BG, fg=TITLE_COLOR).pack(pady=10)
    password_var = tk.StringVar()
    password_entry = tk.Entry(compress_window, textvariable=password_var, show='*')
    password_entry.pack(pady=5)

    def proceed_compression():
        """Validate inputs and start compression process."""
        compression_method = compression_var.get()
        password = password_var.get().strip()
        if not password:
            password = None

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
            start_time = time.time()
            pbar = tqdm(total=100, unit='%', desc="Compressing")
            try:
                def progress_cb(percent, message='Encoding'):
                    elapsed = time.time() - start_time
                    eta = (elapsed / (percent / 100)) - elapsed if percent > 0 else 0
                    eta_str = f"ETA: {int(eta)}s" if eta > 0 else ""
                    root.after(0, lambda: progress_bar.config(value=percent))
                    root.after(0, lambda: progress_label.config(
                        text=f"{message}: {percent:.1f}% {eta_str}"))
                    pbar.n = percent
                    pbar.desc = message
                    pbar.refresh()

                def log_cb(msg):
                    root.after(0, lambda: log_text.insert('1.0', msg + '\n'))

                encode_folder_to_png(
                    folder_path,
                    output_path,
                    compression_method,
                    progress_cb,
                    enable_max_limit=enable_limit_var.get(),
                    password=password,
                    log_callback=log_cb
                )
                pbar.close()
                root.after(0, lambda: messagebox.showinfo(
                    "Success",
                    f"Folder compressed to '{output_path}' "
                    f"using {compression_method.upper()}!"
                ))
            except Exception as e:
                pbar.close()
                root.after(0, lambda e=e: messagebox.showerror(
                    "Error", f"Compression failed: {str(e)}"))
            finally:
                root.after(0, lambda: progress_bar.config(value=0))
                root.after(0, lambda: progress_label.config(text="Idle"))

        threading.Thread(target=encode_worker, daemon=True).start()

    tk.Button(
        compress_window,
        text="Compress",
        command=proceed_compression,
        bg=BUTTON_BG,
        fg=BUTTON_FG,
        font=BUTTON_FONT,
        width=18
    ).pack(pady=15)
    tk.Button(
        compress_window,
        text="Cancel",
        command=compress_window.destroy,
        bg=BUTTON_BG,
        fg=BUTTON_FG,
        font=BUTTON_FONT,
        width=18
    ).pack(pady=5)


def decode_action():
    """
    Handle the extraction action: select PNG and output folder,
    then initiate decoding in background thread.
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

    # Get decode info
    folder_name, file_count, total_size, compression_method, password_info = get_decode_info(img_path)

    # Show confirmation popup
    size_mb = total_size / (1024 * 1024)
    protection = "Password protected" if password_info == "encrypted" else "No password protection"
    message = f"Folder: {folder_name}\nFiles: {file_count}\nTotal size: {size_mb:.2f} MB\nCompression: {compression_method}\nProtection: {protection}\n\nAre you sure you want to extract?"
    if not messagebox.askyesno("Confirm Extraction", message):
        return

    # Prompt for password if needed
    password = None
    if password_info == "encrypted":
        password = simpledialog.askstring("Password Required", "Enter password:", show='*')
        if not password:
            messagebox.showerror("Error", "Password is required for extraction.")
            return

    root.after(0, lambda: log_text.delete('1.0', tk.END))  # Clear log

    def decode_worker():
        start_time = time.time()
        pbar = tqdm(total=100, unit='%', desc="Extracting")
        try:
            def progress_cb(percent, message='Extracting'):
                elapsed = time.time() - start_time
                eta = (elapsed / (percent / 100)) - elapsed if percent > 0 else 0
                eta_str = f"ETA: {int(eta)}s" if eta > 0 else ""
                root.after(0, lambda: progress_bar.config(value=percent))
                root.after(0, lambda: progress_label.config(
                    text=f"{message}: {percent:.1f}% {eta_str}"))
                pbar.n = percent
                pbar.desc = message
                pbar.refresh()

            def log_cb(msg):
                root.after(0, lambda: log_text.insert('1.0', msg + '\n'))

                # Check line count and trim if necessary
                def trim_log():
                    line_count = int(log_text.index('end-1c').split('.')[0])
                    if line_count > 30:
                        log_text.delete('31.0', 'end')
                root.after(50, trim_log)

            decode_png_to_folder(img_path, output_folder, progress_cb, password, log_callback=log_cb)
            pbar.close()
            root.after(0, lambda: messagebox.showinfo(
                "Success", f"Files extracted to '{output_folder}'!"))
        except Exception as e:
            pbar.close()
            root.after(0, lambda e=e: messagebox.showerror(
                "Error", f"Extraction failed: {str(e)}"))
        finally:
            root.after(0, lambda: progress_bar.config(value=0))
            root.after(0, lambda: progress_label.config(text="Idle"))

    threading.Thread(target=decode_worker, daemon=True).start()


def create_main_window():
    """Create and configure the main application window."""
    global root, progress_bar, progress_label, log_text

    root = tk.Tk()
    root.title(WINDOW_TITLE)
    root.geometry(WINDOW_SIZE)
    root.resizable(False, False)
    root.configure(bg=BG_COLOR)

    main_frame = tk.Frame(root, bg=FRAME_BG)
    main_frame.pack(padx=20, pady=20, fill="both", expand=True)

    # Application title
    title_label = tk.Label(
        main_frame,
        text="File Compressor",
        font=TITLE_FONT,
        fg=TITLE_COLOR,
        bg=FRAME_BG
    )
    title_label.pack(pady=(0, 20))

    buttons_frame = tk.Frame(main_frame, bg=FRAME_BG)
    buttons_frame.pack()

    compress_btn = tk.Button(
        buttons_frame,
        text="Compress Folder to PNG",
        command=encode_action,
        font=BUTTON_FONT,
        bg=BUTTON_BG,
        fg=BUTTON_FG,
        width=35,
        relief=tk.RAISED,
        bd=3
    )
    compress_btn.pack(pady=(0, 10))

    extract_btn = tk.Button(
        buttons_frame,
        text="Extract PNG to Folder",
        command=decode_action,
        font=BUTTON_FONT,
        bg=BUTTON_BG,
        fg=BUTTON_FG,
        width=35,
        relief=tk.RAISED,
        bd=3
    )
    extract_btn.pack(pady=(10, 20))

    progress_frame = tk.Frame(main_frame, bg=FRAME_BG)
    progress_frame.pack(pady=(10, 0))

    progress_bar = ttk.Progressbar(
        progress_frame,
        orient="horizontal",
        length=420,
        mode="determinate"
    )
    progress_bar.pack(pady=10)

    progress_label = tk.Label(
        progress_frame,
        text="Idle",
        font=BUTTON_FONT,
        fg=STATUS_COLOR,
        bg=FRAME_BG
    )
    progress_label.pack(pady=10)

    log_label = tk.Label(
        main_frame,
        text="Log:",
        font=LABEL_FONT,
        fg="#FFFFFF",
        bg=FRAME_BG
    )
    log_label.pack(pady=(10, 5))

    log_frame = tk.Frame(main_frame, bg=FRAME_BG)
    log_frame.pack(fill="both", expand=True, padx=10, pady=(0,10))

    log_text = tk.Text(log_frame, bg="#000000", fg="#FFFFFF", font=("Helvetica", 10), height=15, wrap=tk.WORD)
    log_text.pack(fill="both", expand=True)

    footer_label = tk.Label(
        main_frame,
        text="Made by Olibot13 and ChatGPT",
        font=FOOTER_FONT,
        fg=FOOTER_COLOR,
        bg=FRAME_BG
    )
    footer_label.pack(side="bottom", pady=(20, 0))

    root.mainloop()


if __name__ == "__main__":
    create_main_window()
