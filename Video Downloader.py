# title : Video Downloader

import os
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from threading import Thread
from urllib.parse import urlparse
import yt_dlp


class VideoDownloaderApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Smart Video Downloader")
        self.geometry("880x180")
        self.resizable(False, False)
        self.configure(bg="#1e1e1e")

        self.url_var = tk.StringVar()
        self.sort_column = None
        self.sort_ascending = True
        self.downloading_rows = {}
        self.download_folder = None

        self.setup_style()
        self.build_input_frame()

    def setup_style(self):
        self.style = ttk.Style(self)
        self.style.theme_use('clam')
        self.style.configure('TFrame', background='#1e1e1e')
        self.style.configure('TLabel', background='#1e1e1e', foreground='white', font=('Segoe UI', 10))
        self.style.configure('Treeview', background='#2e2e2e', foreground='white',
                             fieldbackground='#2e2e2e', rowheight=28, font=('Segoe UI', 9))
        self.style.configure('Treeview.Heading', background='#444444', foreground='white',
                             font=('Segoe UI', 9, 'bold'))

    def build_input_frame(self):
        self.input_frame = ttk.Frame(self)
        self.input_frame.pack(pady=20, padx=20, fill='x')

        ttk.Label(self.input_frame, text="Enter Video or Playlist URL:").pack(side='left', padx=(0, 10))
        self.url_entry = ttk.Entry(self.input_frame, textvariable=self.url_var, width=60)
        self.url_entry.pack(side='left')

        ttk.Button(self.input_frame, text="Select Folder", command=self.select_download_folder).pack(side='left', padx=5)
        ttk.Button(self.input_frame, text="Fetch Formats", command=self.fetch_info_thread).pack(side='left', padx=5)

        self.loading_label = ttk.Label(self, text="", font=('Segoe UI', 10, 'italic'))
        self.loading_label.pack(pady=(5, 0))

    def select_download_folder(self):
        folder = filedialog.askdirectory(title="Select Download Folder")
        if folder:
            self.download_folder = folder

    def build_results_table(self):
        self.geometry("880x500")

        self.tree = ttk.Treeview(self, columns=("title", "format", "resolution", "filesize", "status"),
                                 show="headings", height=15)
        for col in self.tree["columns"]:
            self.tree.heading(col, text=col.title(), command=lambda _col=col: self.sort_by_column(_col))

        self.tree.column("title", width=300)
        self.tree.column("format", width=80, anchor='center')
        self.tree.column("resolution", width=100, anchor='center')
        self.tree.column("filesize", width=100, anchor='center')
        self.tree.column("status", width=100, anchor='center')

        self.tree.tag_configure('evenrow', background="#2e2e2e")
        self.tree.tag_configure('oddrow', background="#252526")

        self.tree.pack(fill='both', expand=True, padx=20, pady=(10, 10))
        self.tree.bind("<Button-1>", self.on_tree_click)

    def fetch_info_thread(self):
        Thread(target=self.fetch_info).start()

    def fetch_info(self):
        self.loading_label.config(text="Fetching formats, please wait...")
        self.url = self.url_var.get().strip()
        if not self.url:
            messagebox.showerror("Input Error", "Please enter a valid URL.")
            self.loading_label.config(text="")
            return
        if not self.download_folder:
            messagebox.showwarning("Folder Required", "Please select a download folder first.")
            self.loading_label.config(text="")
            return

        try:
            ydl_opts = {
                'quiet': True,
                'extract_flat': False,
                'skip_download': True,
                'forcejson': True,
            }

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(self.url, download=False)

            if not hasattr(self, 'tree'):
                self.build_results_table()
            else:
                for row in self.tree.get_children():
                    self.tree.delete(row)

            entries = info['entries'] if 'entries' in info else [info]
            index = 0
            for video in entries:
                title = video.get('title', 'Unknown')[:50]
                video_url = video.get('webpage_url', self.url)
                formats = video.get('formats', [])

                for fmt in formats:
                    fmt_id = fmt.get('format_id')
                    res = fmt.get('resolution') or fmt.get('format_note') or f"{fmt.get('width', '')}x{fmt.get('height', '')}"
                    size = fmt.get('filesize')
                    size_mb = f"{size / (1024 * 1024):.2f}" if size else "N/A"
                    tag = 'evenrow' if index % 2 == 0 else 'oddrow'

                    display_title = title
                    iid = self.tree.insert("", "end",
                                           values=(display_title, fmt_id, res, size_mb, ""),
                                           tags=(tag, video_url))
                    index += 1

        except Exception as e:
            messagebox.showerror("Error", f"Failed to fetch info:\n{e}")
        finally:
            self.loading_label.config(text="")

    def sort_by_column(self, col):
        data = [(self.tree.set(k, col), k) for k in self.tree.get_children("")]
        try:
            if col == "filesize":
                data.sort(key=lambda t: float(t[0].replace('N/A', '0')), reverse=not self.sort_ascending)
            else:
                data.sort(reverse=not self.sort_ascending)
        except ValueError:
            data.sort(reverse=not self.sort_ascending)
        for index, (val, k) in enumerate(data):
            self.tree.move(k, '', index)
        self.sort_ascending = not self.sort_ascending
        self.sort_column = col

    def on_tree_click(self, event):
        item_id = self.tree.identify_row(event.y)
        col = self.tree.identify_column(event.x)

        if col != "#1" or not item_id:
            return

        if self.downloading_rows.get(item_id):
            messagebox.showinfo("Already Downloading", "This item is already being downloaded.")
            return

        values = self.tree.item(item_id, "values")
        video_url_from_tags = self.tree.item(item_id, "tags")[1]

        Thread(target=self.download_video, args=(item_id, video_url_from_tags, values)).start()
        self.downloading_rows[item_id] = True
        self.tree.set(item_id, "status", "Downloading...")


    def download_video(self, item_id, url, values):
        selected_fmt_id = values[1]
        selected_resolution = values[2]

        title_for_filename = values[0].replace('/', '_').replace('\\', '_').replace(':', '_').replace('*', '_').replace('?', '_').replace('"', '_').replace('<', '_').replace('>', '_').replace('|', '_')
        output_template = os.path.join(self.download_folder, f"{title_for_filename}.%(ext)s")

        def progress_hook(d):
            if d['status'] == 'downloading':
                total_bytes = d.get('total_bytes') or d.get('total_bytes_estimate')
                downloaded_bytes = d.get('downloaded_bytes', 0)
                if total_bytes and downloaded_bytes:
                    progress_percent = downloaded_bytes / total_bytes * 100
                    self.after(0, lambda: self.tree.set(item_id, "status", f"{progress_percent:.1f}%"))
            elif d['status'] == 'finished':
                self.after(0, lambda: self.tree.set(item_id, "status", "✅ Downloaded"))

        if 'p' in selected_resolution.lower() or selected_resolution.lower() == 'n/a':
            format_string = f"bestvideo[height<={selected_resolution.replace('p', '')}][ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best"
        else:
            format_string = f"{selected_fmt_id}+bestaudio/best"

        ydl_opts = {
            'format': format_string,
            'outtmpl': output_template,
            'noplaylist': True,
            'continuedl': True,
            'quiet': False,
            'merge_output_format': 'mp4',
            'progress_hooks': [progress_hook],
            'retries': 3,
            'nooverwrites': True,
            'ffmpeg_location': 'ffmpeg',
            'postprocessors': [{
                'key': 'FFmpegVideoConvertor',
                'preferedformat': 'mp4',
            }],
        }

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
        except Exception as e:
            self.after(0, lambda: self.tree.set(item_id, "status", "❌ Failed"))
            self.after(0, lambda: messagebox.showerror("Download Failed", f"Error downloading {values[0]}:\n{e}"))
        finally:
            self.downloading_rows[item_id] = False


if __name__ == "__main__":
    VideoDownloaderApp().mainloop()