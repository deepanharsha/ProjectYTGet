import os
import tkinter as tk
from tkinter import messagebox, ttk
from pytube import YouTube
import requests
from threading import Thread
print("COPYRIGHTS OF CONTENT DOWNLOADED FROM THIS TOOL IS NOT OURS NOR OUR PROPERTY. WE ARE NOT RESPONSIBLE FOR ANY KINDS OF USAGE OF THIS TOOL OR THE CONTENT IT PROVIDES.");
class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("YouTube Video Downloader")
        self.geometry("400x250")
        
        self.url_label = tk.Label(self, text="Enter YouTube Video URL:")
        self.url_label.pack()
        self.url_entry = tk.Entry(self, width=50)
        self.url_entry.pack()

        self.quality_label = tk.Label(self, text="Select Quality:")
        self.quality_label.pack()
        self.quality_combobox = ttk.Combobox(self, width=47)
        self.quality_combobox['values'] = ['1080p', '720p', '480p', '360p', '240p', '144p']
        self.quality_combobox.current(0)
        self.quality_combobox.pack()

        self.progress_label = tk.Label(self, text="Download Progress:")
        self.progress_label.pack()
        self.progress_bar = ttk.Progressbar(self, orient="horizontal", length=200, mode="determinate")
        self.progress_bar.pack()

        self.download_button = tk.Button(self, text="Download", command=self.download_video)
        self.download_button.pack()

        self.cancel_button = tk.Button(self, text="Cancel", command=self.cancel_download, state="disabled")
        self.cancel_button.pack()

    def download_video(self):
        self.download_button.config(state="disabled")
        self.cancel_button.config(state="normal")

        video_url = self.url_entry.get()
        selected_quality = self.quality_combobox.get()
        save_path = os.path.join(os.path.expanduser("~"), "Videos", "YTGet")

        if not os.path.exists(save_path):
            os.makedirs(save_path)

        try:
            self.yt = YouTube(video_url)
            self.video_stream = self.yt.streams.filter(res=selected_quality, file_extension='mp4').first()
            self.audio_stream = self.yt.streams.filter(only_audio=True).first()

            if self.video_stream and self.audio_stream:
                self.video_filename = os.path.join(save_path, f"{self.yt.title}.mp4")
                self.audio_filename = os.path.join(save_path, f"{self.yt.title}.mp3")

                confirm_msg = f"You're about to download:\n\nTitle: {self.yt.title}\nPublisher: {self.yt.author}\nSize: {self.video_stream.filesize_approx / (1024*1024):.2f} MB\nQuality: {selected_quality}\n\nContinue downloading?"
                confirm_download = messagebox.askyesno("Confirm Download", confirm_msg)

                if confirm_download:
                    messagebox.showinfo("Downloading", f"Downloading: {self.yt.title}")

                    self.download_thread = Thread(target=self.start_download)
                    self.download_thread.start()
            else:
                messagebox.showerror("Error", "Video or audio stream not found.")
        except Exception as e:
            messagebox.showerror("Error", f"Error occurred: {str(e)}")

    def start_download(self):
        try:
            response = requests.get(self.video_stream.url, stream=True)
            total_size_in_bytes = int(response.headers.get('content-length', 0))
            block_size = 1024
            downloaded_bytes = 0
            with open(self.video_filename, 'wb') as f:
                for data in response.iter_content(block_size):
                    f.write(data)
                    downloaded_bytes += len(data)
                    progress = min(int(100 * downloaded_bytes / total_size_in_bytes), 100)
                    self.progress_bar["value"] = progress
                    self.update_idletasks()

            response = requests.get(self.audio_stream.url, stream=True)
            total_size_in_bytes = int(response.headers.get('content-length', 0))
            downloaded_bytes = 0
            with open(self.audio_filename, 'wb') as f:
                for data in response.iter_content(block_size):
                    f.write(data)
                    downloaded_bytes += len(data)
                    progress = min(int(100 * downloaded_bytes / total_size_in_bytes), 100)
                    self.progress_bar["value"] = progress
                    self.update_idletasks()

            # Check if downloaded files exist before merging
            if os.path.exists(self.video_filename) and os.path.exists(self.audio_filename):
                self.merge_audio_and_video(self.video_filename, self.audio_filename)
                os.remove(self.video_filename)
                os.remove(self.audio_filename)

                messagebox.showinfo("Download Complete", "Download completed successfully!")
            else:
                messagebox.showerror("Error", "Downloaded files not found. Please try again.")
        except Exception as e:
            messagebox.showerror("Error", f"Error occurred: {str(e)}")
        finally:
            self.download_button.config(state="normal")
            self.cancel_button.config(state="disabled")

    def merge_audio_and_video(self, video_filename, audio_filename):
        with open(video_filename, 'rb') as f:
            video_data = f.read()
        with open(audio_filename, 'rb') as f:
            audio_data = f.read()

        merged_filename = os.path.splitext(video_filename)[0] + "_ytget.mp4"
        with open(merged_filename, 'wb') as f:
            f.write(video_data)
            f.write(audio_data)

    def cancel_download(self):
        self.download_thread.join()
        os.remove(self.video_filename)
        os.remove(self.audio_filename)
        messagebox.showinfo("Download Canceled", "Download canceled.")
        self.download_button.config(state="normal")
        self.cancel_button.config(state="disabled")

app = App()
app.mainloop()
