import os
import yt_dlp
import asyncio
from collections import deque

from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

TOKEN = os.getenv("BOT_TOKEN")

DOWNLOAD_FOLDER = "downloads"
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)

# =========================
# QUEUE + CACHE
# =========================
queue = deque()
processing = False
cache = set()
user_mode = {}

keyboard = ReplyKeyboardMarkup(
    [["🎬 MP4 Video", "🎵 MP3 Audio"]],
    resize_keyboard=True
)

# =========================
# START
# =========================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Надішли YouTube лінк 👇",
        reply_markup=keyboard
    )

# =========================
# DOWNLOAD CORE
# =========================
def download_video(url, mode):

    base_opts = {
        "outtmpl": f"{DOWNLOAD_FOLDER}/%(title)s.%(ext)s",
        "geo_bypass": True,
        "retries": 5,
        "extractor_retries": 3,
        "http_headers": {
            "User-Agent": "Mozilla/5.0"
        },
    }

    if mode == "mp3":
        base_opts.update({
            "format": "bestaudio/best",
            "postprocessors": [{
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192",
            }],
        })
    else:
        base_opts.update({
            "format": "mp4"
        })

    configs = [
        base_opts,
        {**base_opts, "sleep_interval": 2},
        {**base_opts, "quiet": True}
    ]

    last_error = None

    for cfg in configs:
        try:
            with yt_dlp.YoutubeDL(cfg) as ydl:
                info = ydl.extract_info(url, download=True)
                path = ydl.prepare_filename(info)
                return path
        except Exception as e:
            last_error = e

    raise last_error

# =========================
# QUEUE WORKER
# =========================
async def worker(app):

    global processing

    while True:

        if queue and not processing:

            processing = True
            update, url, mode = queue.popleft()

            try:
                await update.message.reply_text("⏳ Завантажую...")

                path = await asyncio.to_thread(download_video, url, mode)

                if mode == "mp3":
                    path = os.path.splitext(path)[0] + ".mp3"

                if os.path.exists(path):
                    with open(path, "rb") as f:
                        if mode == "mp3":
                            await update.message.reply_audio(f)
                        else:
                            await update.message.reply_video(f)

                    os.remove(path)

            except Exception as e:
                await update.message.reply_text(f"❌ Помилка:\n{e}")

            processing = False

        await asyncio.sleep(1)

# =========================
# HANDLER
# =========================
async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):

    text = update.message.text
    user_id = update.message.from_user.id

    if text == "🎬 MP4 Video":
        user_mode[user_id] = "mp4"
        await update.message.reply_text("MP4 режим")
        return

    if text == "🎵 MP3 Audio":
        user_mode[user_id] = "mp3"
        await update.message.reply_text("MP3 режим")
        return

    if "youtube.com" not in text and "youtu.be" not in text:
        await update.message.reply_text("❌ не YouTube лінк")
        return

    if text in cache:
        await update.message.reply_text("⚠️ вже завантажував це відео")
        return

    cache.add(text)

    mode = user_mode.get(user_id, "mp4")

    queue.append((update, text, mode))

    await update.message.reply_text("📥 Додано в чергу")

# =========================
# APP
# =========================
app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle))

# запуск worker
async def on_startup(app):
    asyncio.create_task(worker(app))

app.post_init = on_startup

print("BOT RUNNING (FREE STABLE MODE)")

app.run_polling()