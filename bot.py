import os
import yt_dlp

from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters
)

# =========================
# TOKEN (Railway env)
# =========================
TOKEN = os.getenv("BOT_TOKEN")

# =========================
# DOWNLOAD FOLDER
# =========================
DOWNLOAD_FOLDER = "downloads"
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)

# =========================
# USER MODE
# =========================
user_mode = {}

# =========================
# KEYBOARD
# =========================
keyboard = ReplyKeyboardMarkup(
    [["🎬 MP4 Video", "🎵 MP3 Audio"]],
    resize_keyboard=True
)

# =========================
# START
# =========================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Надішли YouTube лінк і вибери формат 👇",
        reply_markup=keyboard
    )

# =========================
# FALLBACK DOWNLOADER
# =========================
def download_with_fallback(url, ydl_opts_base):

    configs = [

        # 1. стандартний режим
        ydl_opts_base,

        # 2. браузерний стиль
        {
            **ydl_opts_base,
            "http_headers": {
                "User-Agent": "Mozilla/5.0"
            },
            "sleep_interval": 2,
            "retries": 3,
        },

        # 3. максимально обережний режим
        {
            **ydl_opts_base,
            "quiet": True,
            "no_warnings": True,
            "retries": 5,
            "extractor_retries": 3,
        }
    ]

    last_error = None

    for opts in configs:
        try:
            with yt_dlp.YoutubeDL(opts) as ydl:
                info = ydl.extract_info(url, download=True)
                file_path = ydl.prepare_filename(info)
                return file_path

        except Exception as e:
            last_error = e
            continue

    raise last_error

# =========================
# MAIN HANDLER
# =========================
async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):

    text = update.message.text
    user_id = update.message.from_user.id

    # ---------------------
    # MODE SELECT
    # ---------------------
    if text == "🎬 MP4 Video":
        user_mode[user_id] = "mp4"
        await update.message.reply_text("🎬 MP4 режим увімкнено")
        return

    if text == "🎵 MP3 Audio":
        user_mode[user_id] = "mp3"
        await update.message.reply_text("🎵 MP3 режим увімкнено")
        return

    # ---------------------
    # CHECK LINK
    # ---------------------
    if "youtube.com" not in text and "youtu.be" not in text:
        await update.message.reply_text("❌ Це не YouTube лінк")
        return

    mode = user_mode.get(user_id, "mp4")

    await update.message.reply_text("⏳ Завантажую...")

    try:

        # =====================
        # MP3 MODE
        # =====================
        if mode == "mp3":

            ydl_opts = {
                "format": "bestaudio/best",
                "outtmpl": f"{DOWNLOAD_FOLDER}/%(title)s.%(ext)s",

                "postprocessors": [{
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "mp3",
                    "preferredquality": "192",
                }],

                "geo_bypass": True,
                "concurrent_fragment_downloads": 1,
            }

        # =====================
        # MP4 MODE
        # =====================
        else:

            ydl_opts = {
                "format": "mp4",
                "outtmpl": f"{DOWNLOAD_FOLDER}/%(title)s.%(ext)s",
                "geo_bypass": True,
            }

        # =====================
        # DOWNLOAD (FALLBACK)
        # =====================
        file_path = download_with_fallback(text, ydl_opts)

        # MP3 FIX PATH
        if mode == "mp3":
            base = os.path.splitext(file_path)[0]
            file_path = base + ".mp3"

        # =====================
        # CHECK FILE
        # =====================
        if not os.path.exists(file_path):
            await update.message.reply_text("❌ Файл не знайдено")
            return

        # =====================
        # SEND FILE
        # =====================
        with open(file_path, "rb") as f:
            if mode == "mp3":
                await update.message.reply_audio(f)
            else:
                await update.message.reply_video(f)

        os.remove(file_path)

    except Exception as e:
        await update.message.reply_text(f"❌ Помилка:\n{e}")
        print("ERROR:", e)

# =========================
# APP
# =========================
app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle))

print("BOT RUNNING (STABLE MODE)")

app.run_polling()