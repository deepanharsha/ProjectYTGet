import os
from pathlib import Path

CONFIG = {
    "WINDOW_TITLE": "Project YTGet v1.2",
    "WINDOW_SIZE": "500x320",
    "BG_COLOR": "#1e1e1e",

    "STYLE": {
        "TLabel": {"background": "#1e1e1e", "foreground": "white"},
        "TButton": {"background": "#2d2d2d", "foreground": "white"},
        "TCombobox": {"fieldbackground": "#2d2d2d", "background": "#2d2d2d", "foreground": "white"},
        "TProgressbar": {"troughcolor": "#3e3e3e", "background": "#5cb85c"}
    },

    "ICON_URL": "https://icons.iconarchive.com/icons/dakirby309/windows-8-metro/256/Apps-YouTube-icon.ico",

    "FFMPEG": {
        "WINDOWS": {
            "filename": "ffmpeg.exe",
            "url": "http://dl.dropboxusercontent.com/scl/fi/tjobujcsqk6javukz4hy2/ffmpeg.exe?rlkey=5pfr08n14165w0o4ryt71s2zr&st=7m044mwl&dl=0"
        },
        "LINUX": {
            "filename": "ffmpeg",
            "url": "http://dl.dropboxusercontent.com/scl/fi/84f05ufx2qevdkup2lnj9/ffmpeg?rlkey=mthl9xl48t7985v64uowltfhv&st=4nkivl9l&dl=0"
        }
    },

    "SAVE_DIR": os.path.join(os.path.expanduser("~"), "Videos", "YTGet"),
    "APPDATA_DIR": Path(os.getenv('LOCALAPPDATA') or os.path.expanduser('~/.local/share')) / "YTGet"
}
