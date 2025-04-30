import os
import re
import tkinter as tk
from tkinter import ttk, messagebox
from pytubefix import YouTube
from threading import Thread
import subprocess

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("YouTube Video Downloader")
        self.geometry("550x400")
        self.configure(bg="#1e1e1e")

        style = ttk.Style(self)
        style.theme_use("default")
        style.configure("TLabel", background="#1e1e1e", foreground="#ffffff", font=("Segoe UI", 10))
        style.configure("TButton", font=("Segoe UI", 10))
        style.configure("TCombobox", padding=5)
        style.configure("TProgressbar", thickness=20)

        self.url_label = ttk.Label(self, text="Enter YouTube Video URL:")
        self.url_label.pack(pady=(10, 0))
        self.url_entry = ttk.Entry(self, width=60)
        self.url_entry.pack(pady=5)

        self.fetch_button = ttk.Button(self, text="Fetch Qualities", command=self.fetch_qualities)
        self.fetch_button.pack(pady=5)

        self.quality_label = ttk.Label(self, text="Select Quality:")
        self.quality_label.pack(pady=(15, 0))
        self.quality_combobox = ttk.Combobox(self, width=57)
        self.quality_combobox.pack(pady=5)

        self.progress_label = ttk.Label(self, text="Download Progress:")
        self.progress_label.pack(pady=(15, 0))
        self.progress_bar = ttk.Progressbar(self, orient="horizontal", length=450, mode="determinate")
        self.progress_bar.pack(pady=5)

        self.button_frame = tk.Frame(self, bg="#1e1e1e")
        self.button_frame.pack(pady=10)

        self.download_button = ttk.Button(self.button_frame, text="Download", command=self.download_video)
        self.download_button.grid(row=0, column=0, padx=10)

        self.cancel_button = ttk.Button(self.button_frame, text="Cancel", command=self.cancel_download, state="disabled")
        self.cancel_button.grid(row=0, column=1, padx=10)

        self.video_streams = []
        self.yt = None
        self.download_thread = None
        self.downloading = False

    def fetch_qualities(self):
        url = self.url_entry.get()
        try:
            self.yt = YouTube(url)
            self.video_streams = self.yt.streams.filter(progressive=False, file_extension='mp4', type="video").order_by('resolution').desc()
            resolutions = [stream.resolution for stream in self.video_streams if stream.resolution]
            self.quality_combobox['values'] = resolutions
            if resolutions:
                self.quality_combobox.current(0)
            messagebox.showinfo("Fetched", f"Available qualities for: {self.yt.title}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to fetch qualities: {e}")

    def sanitize_filename(self, title):
        return re.sub(r'[\\/*?"<>|]', '_', title).strip()

    def download_video(self):
        selected_quality = self.quality_combobox.get()
        save_dir = os.path.join(os.path.expanduser("~"), "Videos", "YTGet")
        os.makedirs(save_dir, exist_ok=True)

        title = self.sanitize_filename(self.yt.title)
        video_stream = next((s for s in self.video_streams if s.resolution == selected_quality), None)
        audio_stream = self.yt.streams.filter(only_audio=True, file_extension='mp4').first()

        if not video_stream or not audio_stream:
            messagebox.showerror("Error", "Video or audio stream not found.")
            return

        self.video_path = os.path.join(save_dir, f"{title}_video.mp4")
        self.audio_path = os.path.join(save_dir, f"{title}_audio.mp4")
        self.output_path = os.path.join(save_dir, f"{title}_ytget.mp4")

        self.download_button.config(state="disabled")
        self.cancel_button.config(state="normal")
        self.downloading = True
        self.download_thread = Thread(target=self.download_and_merge, args=(video_stream, audio_stream))
        self.download_thread.start()

    def update_progress(self, value):
        self.progress_bar["value"] = value

    def download_and_merge(self, video_stream, audio_stream):
        try:
            self.after(0, self.update_progress, 0)

            video_stream.download(output_path=os.path.dirname(self.video_path), filename=os.path.basename(self.video_path))
            self.after(0, self.update_progress, 50)

            if not self.downloading:
                return

            audio_stream.download(output_path=os.path.dirname(self.audio_path), filename=os.path.basename(self.audio_path))
            self.after(0, self.update_progress, 75)

            if not self.downloading:
                return

            cmd = [
                "ffmpeg", "-y",
                "-i", self.video_path,
                "-i", self.audio_path,
                "-c:v", "copy", "-c:a", "aac",
                self.output_path
            ]
            subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

            os.remove(self.video_path)
            os.remove(self.audio_path)

            self.after(0, self.update_progress, 100)
            self.after(0, lambda: messagebox.showinfo("Success", f"Download complete: {self.output_path}"))
        except Exception as e:
            self.after(0, lambda: messagebox.showerror("Error", f"Something went wrong: {e}"))
            self.after(0, self.update_progress, 0)
        finally:
            self.after(0, lambda: self.download_button.config(state="normal"))
            self.after(0, lambda: self.cancel_button.config(state="disabled"))
            self.downloading = False

    def cancel_download(self):
        self.downloading = False
        self.download_button.config(state="normal")
        self.cancel_button.config(state="disabled")
        self.progress_bar["value"] = 0
        messagebox.showinfo("Cancelled", "Download cancelled.")

if __name__ == '__main__':
    app = App()
    app.mainloop()
