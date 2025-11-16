import os
import threading
import time
import tkinter as tk
import subprocess
from tkinter import filedialog, messagebox, ttk, simpledialog, scrolledtext
from PIL import Image, ImageTk
Image.MAX_IMAGE_PIXELS = None
from concurrent.futures import ThreadPoolExecutor, as_completed

from tqdm import tqdm

from encoder import encode_folder_to_png
from decoder import decode_png_to_folder, get_decode_info


def check_and_run_autorun_gui(output_folder):
    if os.name == 'nt':
        script_name = 'autorun.bat'
    else:
        script_name = 'autorun.sh'

    script_path = os.path.join(output_folder, script_name)

    if os.path.exists(script_path):
        try:
            with open(script_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            dialog = tk.Toplevel(root)
            dialog.title(f"Autorun Script: {script_name}")
            dialog.geometry("600x500")
            dialog.configure(bg=FRAME_BG)
            text = scrolledtext.ScrolledText(dialog, wrap=tk.WORD, bg="#000000", fg="#FFFFFF")
            text.pack(expand=True, fill='both', padx=10, pady=10)
            text.insert('1.0', content)
            text.config(state='disabled')
            result_var = tk.BooleanVar(value=False)
            def set_result(run):
                result_var.set(run)
                dialog.destroy()
            btn_frame = tk.Frame(dialog, bg=FRAME_BG)
            btn_frame.pack(pady=10)
            tk.Label(btn_frame, text="Do you want to run this script?", fg="#FFFFFF", bg=FRAME_BG).pack()
            tk.Button(btn_frame, text="Yes, Run", command=lambda: set_result(True)).pack(side=tk.LEFT, padx=10)
            tk.Button(btn_frame, text="No, Skip", command=lambda: set_result(False)).pack(side=tk.RIGHT, padx=10)
            root.wait_window(dialog)
            if result_var.get():
                log_text.insert('1.0', f"Running {script_name}...\n")

                def run_script_thread():
                    try:
                        if os.name == 'nt':
                            process = subprocess.Popen(script_path, cwd=output_folder, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, bufsize=1, universal_newlines=True)
                        else:
                            os.chmod(script_path, 0o755)
                            process = subprocess.Popen(['sh', script_path], cwd=output_folder, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, bufsize=1, universal_newlines=True)

                        # Read output in real-time
                        # Real-time output
                        while True:
                            output = process.stdout.readline()
                            if output:
                                root.after(0, lambda: log_text.insert('1.0', f"{output}"))
                            if process.poll() is not None:
                                break

                        # Read any remaining output
                        for line in process.stdout:
                            root.after(0, lambda: log_text.insert('1.0', f"{line}"))
                        for line in process.stderr:
                            root.after(0, lambda: log_text.insert('1.0', f"[ERR] {line}"))

                        if process.returncode == 0:
                            root.after(0, lambda: log_text.insert('1.0', "Script executed successfully.\n"))
                        else:
                            root.after(0, lambda: log_text.insert('1.0', f"Script failed with return code {process.returncode}.\n"))
                    except Exception as e:
                        root.after(0, lambda: log_text.insert('1.0', f"Failed to run script: {e}\n"))

                threading.Thread(target=run_script_thread, daemon=True).start()
            else:
                log_text.insert('1.0', "Script execution skipped.\n")
        except Exception as e:
            root.after(0, lambda e=e: messagebox.showerror("Error", f"Error handling autorun script: {e}"))

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
BUTTON_BG = "#FFFFFF"
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
    global main_frame
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
    folder_name, file_count, total_size, compression_method, password_info, metadata_channels_found = get_decode_info(img_path)

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

    # Create image visualization in main window
    img = Image.open(img_path)
    width, height = img.size
    scale_factor = 650 / max(width, height)
    new_width = int(width * scale_factor)
    new_height = int(height * scale_factor)
    scaled_img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
    canvas = tk.Canvas(main_frame, width=new_width, height=new_height, bg=FRAME_BG)
    canvas.photo = ImageTk.PhotoImage(scaled_img)
    canvas.create_image(0, 0, anchor='nw', image=canvas.photo)
    canvas.grid(row=0, column=1, sticky='nwes')
    main_frame.grid_columnconfigure(1, minsize=new_width, weight=0)
    root.geometry(f"{520 + new_width}x650")  # 500 left + 20 padding + image
    overlays = []
    data_start_idx = metadata_channels_found * 4

    def update_highlight(percent, message='', file='', start_offset=0, end_offset=0):
        progress_bar.config(value=percent)
        progress_label.config(text=message)
        # Clear previous overlays
        for ov in overlays:
            canvas.delete(ov)
        overlays.clear()
        if file and start_offset < end_offset:
            # Calculate pixel range
            byte_start = data_start_idx + start_offset
            pixel_start = byte_start // 4
            x1 = pixel_start % width
            y1 = pixel_start // width
            byte_end = data_start_idx + end_offset - 1
            pixel_end = byte_end // 4
            x2 = pixel_end % width
            y2 = pixel_end // width
            sx1 = int(x1 * new_width / width)
            sy1 = int(y1 * new_height / height)
            sx2 = int((x2 + 1) * new_width / width)
            sy2 = int((y2 + 1) * new_height / height)
            overlays.append(canvas.create_rectangle(sx1, sy1, sx2, sy2, outline='red', width=3))
            if sx2 - sx1 > 100 and sy2 - sy1 > 50:
                overlays.append(canvas.create_text((sx1 + sx2)//2, (sy1 + sy2)//2, text=f"Processing: {os.path.basename(file)}", fill='red', font=('Helvetica', 14, 'bold')))
        root.update_idletasks()

    def decode_worker():
        try:
            def log_cb(msg):
                root.after(0, lambda: log_text.insert('1.0', msg + '\n'))

                # Check line count and trim if necessary
                def trim_log():
                    line_count = int(log_text.index('end-1c').split('.')[0])
                    if line_count > 30:
                        log_text.delete('31.0', 'end')
                root.after(50, trim_log)

            decode_png_to_folder(img_path, output_folder, update_highlight, password, log_callback=log_cb)
            root.after(0, lambda output_folder=output_folder: check_and_run_autorun_gui(output_folder))
            root.after(0, lambda: messagebox.showinfo(
                "Success", f"Files extracted to '{output_folder}'!"))
        except Exception as e:
            root.after(0, lambda e=e: messagebox.showerror(
                "Error", f"Extraction failed: {str(e)}"))
        finally:
            root.after(0, lambda: progress_bar.config(value=0))
            root.after(0, lambda: progress_label.config(text="Idle"))
            canvas.grid_remove()
            root.geometry(WINDOW_SIZE)
            main_frame.grid_columnconfigure(1, minsize=0)

    threading.Thread(target=decode_worker, daemon=True).start()


def create_main_window():
    """Create and configure the main application window."""
    global root, progress_bar, progress_label, log_text, main_frame

    root = tk.Tk()
    root.title(WINDOW_TITLE)
    root.geometry(WINDOW_SIZE)
    root.resizable(False, False)
    root.configure(bg=BG_COLOR)

    main_frame = tk.Frame(root, bg=FRAME_BG)
    main_frame.pack(padx=20, pady=20, fill="both", expand=True)
    main_frame.grid_columnconfigure(0, weight=0, minsize=500)
    main_frame.grid_columnconfigure(1, weight=0)
    main_frame.grid_rowconfigure(0, weight=1)

    left_frame = tk.Frame(main_frame, bg=FRAME_BG, width=500)
    left_frame.grid(row=0, column=0, sticky='nwes')
    left_frame.pack_propagate(False)

    # Application title
    title_label = tk.Label(
        left_frame,
        text="File Compressor",
        font=TITLE_FONT,
        fg=TITLE_COLOR,
        bg=FRAME_BG
    )
    title_label.pack(pady=(0, 20))

    buttons_frame = tk.Frame(left_frame, bg=FRAME_BG)
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

    progress_frame = tk.Frame(left_frame, bg=FRAME_BG)
    progress_frame.pack(pady=10)

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
        left_frame,
        text="Log:",
        font=LABEL_FONT,
        fg="#FFFFFF",
        bg=FRAME_BG
    )
    log_label.pack(pady=(10,5))

    log_frame = tk.Frame(left_frame, bg=FRAME_BG)
    log_frame.pack(fill="both", expand=True, padx=10, pady=(0,10))

    log_text = tk.Text(log_frame, bg="#000000", fg="#FFFFFF", font=("Helvetica", 10), height=15, wrap=tk.WORD)
    log_text.pack(fill="both", expand=True)

    footer_label = tk.Label(
        left_frame,
        text="Made by Olibot13 and ChatGPT",
        font=FOOTER_FONT,
        fg=FOOTER_COLOR,
        bg=FRAME_BG
    )
    footer_label.pack(side="bottom", pady=20)

    root.mainloop()


if __name__ == "__main__":
    create_main_window()
