import yt_dlp
import os

DOWNLOAD_FOLDER = "downloads"
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)

def download_video(url, mode):

    base = {
        "outtmpl": f"{DOWNLOAD_FOLDER}/%(title)s.%(ext)s",
        "retries": 5,
        "extractor_retries": 3,
        "geo_bypass": True,
        "http_headers": {
            "User-Agent": "Mozilla/5.0"
        }
    }

    if mode == "mp3":
        base.update({
            "format": "bestaudio/best",
            "postprocessors": [{
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192"
            }]
        })
    else:
        base.update({"format": "mp4"})

    configs = [
        base,
        {**base, "sleep_interval": 2},
        {**base, "quiet": True}
    ]

    for cfg in configs:
        try:
            with yt_dlp.YoutubeDL(cfg) as ydl:
                info = ydl.extract_info(url, download=True)
                path = ydl.prepare_filename(info)
                return path
        except:
            continue

    raise Exception("Download failed")