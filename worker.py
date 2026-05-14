import asyncio
import os
from downloader import download_video

queue = []

async def worker(bot):

    while True:

        if queue:

            job = queue.pop(0)

            url = job["url"]
            mode = job["mode"]
            chat_id = job["chat_id"]

            try:
                path = download_video(url, mode)

                if mode == "mp3":
                    path = os.path.splitext(path)[0] + ".mp3"

                with open(path, "rb") as f:
                    if mode == "mp3":
                        await bot.send_audio(chat_id=chat_id, audio=f)
                    else:
                        await bot.send_video(chat_id=chat_id, video=f)

                os.remove(path)

            except Exception as e:
                await bot.send_message(chat_id=chat_id, text=f"error: {e}")

        await asyncio.sleep(2)