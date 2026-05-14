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
# ПАПКА ДЛЯ ФАЙЛІВ
# =========================
DOWNLOAD_FOLDER = "downloads"
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)

# =========================
# РЕЖИМ КОРИСТУВАЧА
# =========================
user_mode = {}

# =========================
# КНОПКИ
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
# ОСНОВНА ЛОГІКА
# =========================
async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):

    text = update.message.text
    user_id = update.message.from_user.id

    # -------------------------
    # MP4 MODE
    # -------------------------
    if text == "🎬 MP4 Video":

        user_mode[user_id] = "mp4"

        await update.message.reply_text(
            "🎬 MP4 режим увімкнено. Надішли посилання."
        )

        return

    # -------------------------
    # MP3 MODE
    # -------------------------
    if text == "🎵 MP3 Audio":

        user_mode[user_id] = "mp3"

        await update.message.reply_text(
            "🎵 MP3 режим увімкнено. Надішли посилання."
        )

        return

    # -------------------------
    # CHECK LINK
    # -------------------------
    if "youtube.com" not in text and "youtu.be" not in text:

        await update.message.reply_text(
            "❌ Це не YouTube посилання."
        )

        return

    mode = user_mode.get(user_id, "mp4")

    await update.message.reply_text("⏳ Завантажую...")

    try:

        # =========================
        # MP3 MODE
        # =========================
        if mode == "mp3":

            ydl_opts = {
                "format": "bestaudio/best",
                "outtmpl": f"{DOWNLOAD_FOLDER}/%(title)s.%(ext)s",

                "postprocessors": [{
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "mp3",
                    "preferredquality": "192",
                }],

                "prefer_ffmpeg": True,
                "keepvideo": False,
            }

        # =========================
        # MP4 MODE
        # =========================
        else:

            ydl_opts = {
                "format": "mp4",
                "outtmpl": f"{DOWNLOAD_FOLDER}/%(title)s.%(ext)s",
            }

        # =========================
        # DOWNLOAD
        # =========================
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:

            info = ydl.extract_info(text, download=True)

            file_path = ydl.prepare_filename(info)

            # MP3 fix path
            if mode == "mp3":
                base = os.path.splitext(file_path)[0]
                file_path = base + ".mp3"

        # =========================
        # CHECK FILE
        # =========================
        if not os.path.exists(file_path):

            await update.message.reply_text("❌ Файл не знайдено.")

            return

        # =========================
        # SEND FILE
        # =========================
        with open(file_path, "rb") as f:

            if mode == "mp3":
                await update.message.reply_audio(f)
            else:
                await update.message.reply_video(f)

        # =========================
        # CLEANUP
        # =========================
        os.remove(file_path)

    except Exception as e:

        await update.message.reply_text(f"❌ Помилка:\n{e}")

        print("ERROR:", e)

# =========================
# APP
# =========================
app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))

app.add_handler(
    MessageHandler(filters.TEXT & ~filters.COMMAND, handle)
)

print("BOT RUNNING (PRODUCTION MODE)")

app.run_polling()