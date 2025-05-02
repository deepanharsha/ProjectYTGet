import os
import re
import sys
import tkinter as tk
from tkinter import ttk, messagebox
from pytubefix import YouTube
from threading import Thread
import subprocess
import urllib.request
from pathlib import Path
from urllib.error import URLError


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Project YTGet v1.2")
        self.geometry("500x320")
        self.configure(bg="#1e1e1e")

        self.icon_path = self.setup_icon()
        if self.icon_path:
            try:
                self.iconbitmap(self.icon_path)
            except:
                pass

        style = ttk.Style()
        style.theme_use('default')
        style.configure("TLabel", background="#1e1e1e", foreground="white")
        style.configure("TButton", background="#2d2d2d", foreground="white")
        style.configure("TCombobox", fieldbackground="#2d2d2d", background="#2d2d2d", foreground="white")
        style.configure("TProgressbar", troughcolor="#3e3e3e", background="#5cb85c")

        self.create_widgets()

        self.video_streams = []
        self.yt = None
        self.ffmpeg_path = self.get_ffmpeg_path()
        self.current_thread = None
        self.download_cancelled = False
        self.popup = None
        self.popup_bar = None

    def create_widgets(self):
        self.url_label = ttk.Label(self, text="Enter YouTube Video URL:")
        self.url_label.pack(pady=(10, 0))
        self.url_entry = ttk.Entry(self, width=60)
        self.url_entry.pack(pady=2)

        self.fetch_button = ttk.Button(self, text="Fetch Qualities", command=self.fetch_qualities)
        self.fetch_button.pack(pady=2)

        self.quality_label = ttk.Label(self, text="Select Quality:")
        self.quality_label.pack(pady=(10, 0))
        self.quality_combobox = ttk.Combobox(self, width=57)
        self.quality_combobox.pack(pady=2)

        self.progress_label = ttk.Label(self, text="Download Progress:")
        self.progress_label.pack(pady=(10, 0))
        self.progress_bar = ttk.Progressbar(self, orient="horizontal", length=400, mode="determinate")
        self.progress_bar.pack(pady=2)

        self.download_button = ttk.Button(self, text="Download", command=self.download_video)
        self.download_button.pack(pady=5)

        self.cancel_button = ttk.Button(self, text="Cancel", command=self.cancel_download, state="disabled")
        self.cancel_button.pack(pady=2)

    def setup_icon(self):
        try:
            appdata = Path(os.getenv('LOCALAPPDATA') or os.path.expanduser('~/.local/share')) / "YTGet"
            appdata.mkdir(parents=True, exist_ok=True)
            icon_path = appdata / "icon.ico"
            if not icon_path.exists():
                urllib.request.urlretrieve(
                    "https://icons.iconarchive.com/icons/dakirby309/windows-8-metro/256/Apps-YouTube-icon.ico",
                    icon_path
                )
            return str(icon_path)
        except Exception:
            return None

    def get_ffmpeg_path(self):
        appdata_path = Path(os.getenv('LOCALAPPDATA') or os.path.expanduser('~/.local/share')) / "YTGet"
        appdata_path.mkdir(parents=True, exist_ok=True)
        ffmpeg_exe = appdata_path / ("ffmpeg.exe" if os.name == "nt" else "ffmpeg")

        if not ffmpeg_exe.exists():
            try:
                url = "https://3333.filelu.live/d/rf3avs2rjrie7jtaa2niszvxrb24lry5gsslxu5ksutks7wwhe7tr5ipuweavmq5fy2zq5mm/ffmpeg.exe"
                self.start_progress_popup("Downloading FFmpeg...")
                urllib.request.urlretrieve(url, ffmpeg_exe, self.download_progress)
                self.close_progress_popup("FFmpeg Downloaded")
            except URLError as e:
                self.close_progress_popup("Error")
                messagebox.showerror("Download Error", f"Failed to download FFmpeg: {e}")
        return str(ffmpeg_exe)

    def fetch_qualities(self):
        url = self.url_entry.get().strip()
        try:
            self.yt = YouTube(url)
            self.video_streams = self.yt.streams.filter(progressive=False, file_extension='mp4', type="video").order_by('resolution').desc()
            resolutions = [s.resolution for s in self.video_streams if s.resolution]
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
        if not selected_quality:
            messagebox.showerror("Error", "Please select a quality first.")
            return

        title = self.sanitize_filename(self.yt.title)
        save_dir = os.path.join(os.path.expanduser("~"), "Videos", "YTGet")
        os.makedirs(save_dir, exist_ok=True)

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
        self.download_cancelled = False

        self.current_thread = Thread(target=self.download_and_merge, args=(video_stream, audio_stream))
        self.current_thread.start()

    def update_progress(self, value):
        self.progress_bar["value"] = value
        self.progress_bar.update()

    def start_progress_popup(self, message):
        self.popup = tk.Toplevel(self)
        self.popup.title("Please wait...")
        self.popup.geometry("300x100")
        self.popup.configure(bg="#2e2e2e")
        tk.Label(self.popup, text=message, bg="#2e2e2e", fg="white").pack(pady=10)
        self.popup_bar = ttk.Progressbar(self.popup, orient="horizontal", length=250, mode="determinate")
        self.popup_bar.pack(pady=5)
        self.popup_bar["value"] = 0
        self.popup.update()

    def download_progress(self, block_num, block_size, total_size):
        downloaded = block_num * block_size
        percent = int((downloaded / total_size) * 100) if total_size > 0 else 0
        if self.popup_bar:
            self.popup_bar["value"] = percent
            self.popup.update()

    def close_progress_popup(self, final_message):
        if self.popup:
            self.popup.destroy()
            self.popup = None
            self.popup_bar = None
        messagebox.showinfo("Done", final_message)

    def cancel_download(self):
        self.download_cancelled = True
        messagebox.showinfo("Cancelled", "Download will stop soon.")
        self.cancel_button.config(state="disabled")

    def download_and_merge(self, video_stream, audio_stream):
        try:
            self.after(0, self.update_progress, 0)
            if self.download_cancelled: return

            video_stream.download(filename=self.video_path)
            self.after(0, self.update_progress, 50)
            if self.download_cancelled: return

            audio_stream.download(filename=self.audio_path)
            self.after(0, self.update_progress, 75)
            if self.download_cancelled: return

            cmd = [
                self.ffmpeg_path, "-y",
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
        finally:
            self.after(0, lambda: self.download_button.config(state="normal"))
            self.after(0, lambda: self.cancel_button.config(state="disabled"))


if __name__ == '__main__':
    app = App()
    app.mainloop()
