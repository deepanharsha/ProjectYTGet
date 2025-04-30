import os
import tkinter as tk
from tkinter import ttk, messagebox
from pytube import YouTube
from moviepy.editor import VideoFileClip, AudioFileClip
from threading import Thread
import re

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("YouTube Video Downloader")
        self.geometry("450x280")
        self.cancel_flag = False

        tk.Label(self, text="Enter YouTube Video URL:").pack()
        self.url_entry = tk.Entry(self, width=55)
        self.url_entry.pack()

        tk.Label(self, text="Select Quality:").pack()
        self.quality_combobox = ttk.Combobox(self, width=50, values=['1080p', '720p', '480p', '360p', '240p', '144p'])
        self.quality_combobox.current(0)
        self.quality_combobox.pack()

        tk.Label(self, text="Download Progress:").pack()
        self.progress_bar = ttk.Progressbar(self, length=300, mode="determinate")
        self.progress_bar.pack(pady=5)

        self.download_button = tk.Button(self, text="Download", command=self.download_video)
        self.download_button.pack(pady=5)

        self.cancel_button = tk.Button(self, text="Cancel", command=self.cancel_download, state="disabled")
        self.cancel_button.pack()

    def sanitize_filename(self, title):
        return re.sub(r'[\\/*?:"<>|]', "_", title)

    def download_video(self):
        self.download_button.config(state="disabled")
        self.cancel_button.config(state="normal")
        self.cancel_flag = False

        url = self.url_entry.get().strip()
        quality = self.quality_combobox.get()

        Thread(target=self._download_video_thread, args=(url, quality)).start()

    def _download_video_thread(self, url, quality):
        try:
            yt = YouTube(url, on_progress_callback=self.on_progress)
            title = self.sanitize_filename(yt.title)
            save_dir = os.path.join(os.path.expanduser("~"), "Videos", "YTGet")
            os.makedirs(save_dir, exist_ok=True)

            video_stream = yt.streams.filter(res=quality, mime_type='video/mp4', progressive=False).first()
            audio_stream = yt.streams.filter(only_audio=True, mime_type='audio/mp4').first()

            if not video_stream or not audio_stream:
                messagebox.showerror("Stream Not Found", "Couldn't find the selected quality or audio.")
                return

            confirm = messagebox.askyesno("Confirm Download", f"Download:\n{yt.title}\nQuality: {quality}?")
            if not confirm:
                return

            video_path = os.path.join(save_dir, f"{title}_video.mp4")
            audio_path = os.path.join(save_dir, f"{title}_audio.mp4")
            output_path = os.path.join(save_dir, f"{title}_ytget.mp4")

            video_stream.download(filename=video_path)
            audio_stream.download(filename=audio_path)

            if self.cancel_flag:
                return

            video_clip = VideoFileClip(video_path)
            audio_clip = AudioFileClip(audio_path)
            final_clip = video_clip.set_audio(audio_clip)
            final_clip.write_videofile(output_path, codec='libx264', audio_codec='aac')

            video_clip.close()
            audio_clip.close()
            os.remove(video_path)
            os.remove(audio_path)

            messagebox.showinfo("Done", f"Downloaded: {output_path}")

        except Exception as e:
            messagebox.showerror("Error", str(e))
        finally:
            self.download_button.config(state="normal")
            self.cancel_button.config(state="disabled")
            self.progress_bar["value"] = 0

    def on_progress(self, stream, chunk, bytes_remaining):
        total = stream.filesize
        percent = int(((total - bytes_remaining) / total) * 100)
        self.progress_bar["value"] = percent
        self.update_idletasks()

    def cancel_download(self):
        self.cancel_flag = True
        messagebox.showinfo("Cancelled", "Download cancelled.")
        self.download_button.config(state="normal")
        self.cancel_button.config(state="disabled")

if __name__ == "__main__":
    print("COPYRIGHT NOTICE: You are solely responsible for how you use this tool.")
    app = App()
    app.mainloop()
