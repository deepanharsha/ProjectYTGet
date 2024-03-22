import os
from pytube import YouTube

def download_video(video_url, save_path):
    try:
        yt = YouTube(video_url)
        stream = yt.streams.get_highest_resolution()
        print("Downloading:", yt.title)
        stream.download(output_path=save_path)
        print("Download completed successfully!")
    except Exception as e:
        print("Error occurred:", str(e))

if __name__ == "__main__":
    video_url = input("Enter the YouTube video URL: ")
    user_folder = os.path.expanduser("~")
    save_path = os.path.join(user_folder, "Videos", "YTGet")
    
    if not os.path.exists(save_path):
        os.makedirs(save_path)
        print("Created directory:", save_path)

    download_video(video_url, save_path)
