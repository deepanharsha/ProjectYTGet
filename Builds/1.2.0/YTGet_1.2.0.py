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
from PIL import Image, ImageTk


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Project YTGet 1.2.0")
        self.geometry("520x360")
        self.configure(bg="#1e1e1e")
        self.resizable(False, False)

        # Set window icon from icon.png (must be in same folder)
        try:
            self.icon_img = tk.PhotoImage(file="icon.png")
            self.iconphoto(False, self.icon_img)
        except Exception as e:
            print(f"Error loading window icon: {e}")

        # Load dark/light mode icons (webp -> PhotoImage)
        try:
            dark_icon_img = Image.open("darkmode.png").resize((24, 24), Image.Resampling.LANCZOS)
            self.dark_icon = ImageTk.PhotoImage(dark_icon_img)
            light_icon_img = Image.open("lightmode.webp").resize((24, 24), Image.Resampling.LANCZOS)
            self.light_icon = ImageTk.PhotoImage(light_icon_img)
        except Exception as e:
            print(f"Error loading dark/light mode icons: {e}")
            self.dark_icon = None
            self.light_icon = None

        # State for theme: True = Dark, False = Light
        self.is_dark_mode = True

        # Setup style
        self.style = ttk.Style()
        self.set_theme(self.is_dark_mode)

        self.create_widgets()

        self.video_streams = []
        self.yt = None
        self.ffmpeg_path = self.get_ffmpeg_path()
        self.current_thread = None
        self.download_cancelled = False
        self.popup = None
        self.popup_bar = None

        self.protocol("WM_DELETE_WINDOW", self.on_closing)

    def set_theme(self, dark_mode: bool):
        # Define colors for dark/light mode
        if dark_mode:
            bg = "#1e1e1e"
            fg = "white"
            btn_bg = "#2d2d2d"
            cb_bg = "#2d2d2d"
            progress_bg = "#5cb85c"
            trough_bg = "#3e3e3e"
            entry_bg = "#2d2d2d"
            label_bg = bg
        else:
            bg = "white"
            fg = "black"
            btn_bg = "#e0e0e0"
            cb_bg = "white"
            progress_bg = "#4caf50"
            trough_bg = "#c0c0c0"
            entry_bg = "white"
            label_bg = bg

        self.configure(bg=bg)
        style = self.style
        style.theme_use('default')
        style.configure("TLabel", background=label_bg, foreground=fg)
        style.configure("TButton", background=btn_bg, foreground=fg)
        style.map("TButton",
                  background=[('active', '#4a90e2' if dark_mode else '#a0c4ff')],
                  foreground=[('active', 'white' if dark_mode else 'black')])
        style.configure("TCombobox",
                        fieldbackground=cb_bg,
                        background=cb_bg,
                        foreground=fg)
        style.configure("TEntry",
                        fieldbackground=entry_bg,
                        foreground=fg)
        style.configure("TProgressbar", troughcolor=trough_bg, background=progress_bg)

    def toggle_mode(self):
        self.is_dark_mode = not self.is_dark_mode
        self.set_theme(self.is_dark_mode)

        # Update background colors of some widgets manually
        self.url_entry.configure(background=self.style.lookup("TEntry", "fieldbackground"))
        self.quality_combobox.configure(background=self.style.lookup("TCombobox", "fieldbackground"))
        self.progress_bar.configure(style="TProgressbar")

        # Update icon on the toggle button
        if self.is_dark_mode:
            if self.dark_icon:
                self.mode_button.config(image=self.dark_icon)
            self.configure(bg="#1e1e1e")
        else:
            if self.light_icon:
                self.mode_button.config(image=self.light_icon)
            self.configure(bg="white")

    def create_widgets(self):
        pad_y = 8
        pad_x = 10

        self.url_label = ttk.Label(self, text="Enter YouTube Video URL:")
        self.url_label.pack(pady=(15, 2), padx=pad_x, anchor='w')

        self.url_entry = ttk.Entry(self, width=65)
        self.url_entry.pack(pady=2, padx=pad_x, fill='x')

        self.fetch_button = ttk.Button(self, text="Fetch Qualities", command=self.fetch_qualities)
        self.fetch_button.pack(pady=pad_y, padx=pad_x, fill='x')

        self.quality_label = ttk.Label(self, text="Select Quality:")
        self.quality_label.pack(pady=(15, 2), padx=pad_x, anchor='w')

        self.quality_combobox = ttk.Combobox(self, width=62, state="readonly")
        self.quality_combobox.pack(pady=2, padx=pad_x, fill='x')

        self.progress_label = ttk.Label(self, text="Download Progress:")
        self.progress_label.pack(pady=(15, 2), padx=pad_x, anchor='w')

        self.progress_bar = ttk.Progressbar(self, orient="horizontal", length=480, mode="determinate")
        self.progress_bar.pack(pady=2, padx=pad_x, fill='x')

        btn_frame = tk.Frame(self, bg=self['bg'])
        btn_frame.pack(pady=15, padx=pad_x, fill='x')

        self.download_button = ttk.Button(btn_frame, text="Download", command=self.download_video)
        self.download_button.pack(side='left', fill='x', expand=True, padx=(0,5))

        self.cancel_button = ttk.Button(btn_frame, text="Cancel", command=self.cancel_download, state="disabled")
        self.cancel_button.pack(side='left', fill='x', expand=True, padx=(5,0))

        # Dark/light mode toggle button bottom right
        mode_frame = tk.Frame(self, bg=self['bg'])
        mode_frame.pack(side='bottom', anchor='e', padx=10, pady=5)

        self.mode_button = ttk.Button(mode_frame, width=30, command=self.toggle_mode)
        if self.dark_icon:
            self.mode_button.config(image=self.dark_icon)
        else:
            self.mode_button.config(text="Toggle Mode")
        self.mode_button.pack()

    def get_ffmpeg_path(self):
        appdata_path = Path(os.getenv('LOCALAPPDATA') or os.path.expanduser('~/.local/share')) / "YTGet"
        appdata_path.mkdir(parents=True, exist_ok=True)

        if os.name == "nt":
            ffmpeg_filename = "ffmpeg.exe"
            ffmpeg_url = "http://dl.dropboxusercontent.com/scl/fi/tjobujcsqk6javukz4hy2/ffmpeg.exe?rlkey=5pfr08n14165w0o4ryt71s2zr&st=7m044mwl&dl=0"
        else:
            ffmpeg_filename = "ffmpeg"
            ffmpeg_url = "http://dl.dropboxusercontent.com/scl/fi/84f05ufx2qevdkup2lnj9/ffmpeg?rlkey=mthl9xl48t7985v64uowltfhv&st=4nkivl9l&dl=0"

        ffmpeg_exe = appdata_path / ffmpeg_filename

        if not ffmpeg_exe.exists():
            try:
                self.start_progress_popup("Downloading FFmpeg...")
                urllib.request.urlretrieve(ffmpeg_url, ffmpeg_exe, self.download_progress)
                if os.name != "nt":
                    ffmpeg_exe.chmod(0o755)
                self.close_progress_popup("FFmpeg Downloaded")
            except URLError as e:
                self.close_progress_popup("Error")
                messagebox.showerror("Download Error", f"Failed to download FFmpeg: {e}")
        return str(ffmpeg_exe)

    def fetch_qualities(self):
        url = self.url_entry.get().strip()
        if not url:
            messagebox.showerror("Error", "Please enter a YouTube video URL.")
            return

        try:
            self.yt = YouTube(url)
            self.video_streams = self.yt.streams.filter(progressive=False, file_extension='mp4', type="video").order_by('resolution').desc()
            resolutions = [s.resolution for s in self.video_streams if s.resolution]
            self.quality_combobox['values'] = resolutions
            if resolutions:
                self.quality_combobox.current(0)
            messagebox.showinfo("Fetched", f"Available qualities for:\n{self.yt.title}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to fetch qualities: {e}")

    def sanitize_filename(self, title):
        return re.sub(r'[\\/*?"<>|]', '_', title).strip()

    def download_video(self):
        selected_quality = self.quality_combobox.get()
        if not selected_quality:
            messagebox.showerror("Error", "Please select a quality first.")
            return
        if not self.yt:
            messagebox.showerror("Error", "Please fetch qualities first.")
            return

        title = self.sanitize_filename(self.yt.title)
        if len(title) > 180:
            title = title[:180]

        save_dir = os.path.join(os.path.expanduser("~"), "Videos", "YTGet")
        os.makedirs(save_dir, exist_ok=True)

        video_stream = next((s for s in self.video_streams if s.resolution == selected_quality), None)
        audio_stream = self.yt.streams.filter(only_audio=True, file_extension='mp4').first()

        if not video_stream or not audio_stream:
            messagebox.showerror("Error", "Video or audio stream not found.")
            return

        self.video_filename = f"{title}_video.mp4"
        self.audio_filename = f"{title}_audio.mp4"
        self.output_filename = f"{title}_ytget.mp4"

        self.video_path = os.path.join(save_dir, self.video_filename)
        self.audio_path = os.path.join(save_dir, self.audio_filename)
        self.output_path = os.path.join(save_dir, self.output_filename)

        if os.path.exists(self.output_path):
            overwrite = messagebox.askyesno("File Exists", "Output file already exists. Overwrite?")
            if not overwrite:
                return

        self.download_button.config(state="disabled")
        self.cancel_button.config(state="normal")
        self.download_cancelled = False
        self.progress_bar["value"] = 0

        self.current_thread = Thread(target=self.download_and_merge, args=(video_stream, audio_stream, save_dir))
        self.current_thread.start()

    def update_progress(self, value):
        self.progress_bar["value"] = value
        self.progress_bar.update()

    def start_progress_popup(self, message):
        self.popup = tk.Toplevel(self)
        self.popup.title("Please wait...")
        self.popup.geometry("300x100")
        self.popup.configure(bg=self['bg'])
        tk.Label(self.popup, text=message, bg=self['bg'], fg=self.style.lookup("TLabel", "foreground")).pack(pady=10)
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

    def download_url_to_file(self, url, filepath):
        try:
            with urllib.request.urlopen(url) as response, open(filepath, 'wb') as out_file:
                total_length = response.getheader('Content-Length')
                total_length = int(total_length.strip()) if total_length else 0
                bytes_downloaded = 0
                chunk_size = 65536  # bigger chunk for speed

                while True:
                    if self.download_cancelled:
                        raise Exception("Download cancelled by user")

                    chunk = response.read(chunk_size)
                    if not chunk:
                        break

                    out_file.write(chunk)
                    bytes_downloaded += len(chunk)

                    if total_length > 0:
                        progress = int((bytes_downloaded / total_length) * 100)
                        self.after(0, self.update_progress, progress)
            return True
        except Exception as e:
            # Clean partial file on cancel or error
            if os.path.exists(filepath):
                try:
                    os.remove(filepath)
                except:
                    pass
            raise e

    def download_and_merge(self, video_stream, audio_stream, save_dir):
        try:
            self.after(0, self.update_progress, 0)
            if self.download_cancelled:
                return

            # Download video with cancel support
            self.download_url_to_file(video_stream.url, self.video_path)
            self.after(0, self.update_progress, 50)
            if self.download_cancelled:
                return

            # Download audio with cancel support
            self.download_url_to_file(audio_stream.url, self.audio_path)
            self.after(0, self.update_progress, 75)
            if self.download_cancelled:
                return

            # Merge with ffmpeg
            cmd = [
                self.ffmpeg_path, "-y",
                "-i", self.video_path,
                "-i", self.audio_path,
                "-c:v", "copy", "-c:a", "aac",
                self.output_path
            ]
            subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

            # Clean temp files
            try:
                os.remove(self.video_path)
            except:
                pass
            try:
                os.remove(self.audio_path)
            except:
                pass

            self.after(0, self.update_progress, 100)
            self.after(0, lambda: messagebox.showinfo("Success", f"Download complete: {self.output_path}"))
        except Exception as e:
            if str(e) == "Download cancelled by user":
                self.after(0, lambda: messagebox.showinfo("Cancelled", "Download cancelled successfully."))
            else:
                self.after(0, lambda: messagebox.showerror("Error", f"Something went wrong: {e}"))
        finally:
            self.after(0, lambda: self.download_button.config(state="normal"))
            self.after(0, lambda: self.cancel_button.config(state="disabled"))
            self.download_cancelled = False
            self.after(0, self.update_progress, 0)

    def on_closing(self):
        if self.current_thread and self.current_thread.is_alive():
            if messagebox.askyesno("Quit", "A download is in progress. Quit anyway?"):
                self.download_cancelled = True
                self.destroy()
        else:
            self.destroy()


if __name__ == '__main__':
    app = App()
    app.mainloop()
