import os
import asyncio
from collections import deque

from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

TOKEN = os.getenv("BOT_TOKEN")

queue = deque()
user_mode = {}

keyboard = ReplyKeyboardMarkup(
    [["🎬 MP4", "🎵 MP3"]],
    resize_keyboard=True
)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Кидай YouTube лінк", reply_markup=keyboard)

async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    user_id = update.message.from_user.id

    if text == "🎬 MP4":
        user_mode[user_id] = "mp4"
        await update.message.reply_text("MP4 режим")
        return

    if text == "🎵 MP3":
        user_mode[user_id] = "mp3"
        await update.message.reply_text("MP3 режим")
        return

    if "youtube.com" not in text and "youtu.be" not in text:
        await update.message.reply_text("це не YouTube")
        return

    mode = user_mode.get(user_id, "mp4")

    queue.append({
        "url": text,
        "mode": mode,
        "chat_id": update.message.chat_id
    })

    await update.message.reply_text("додано в чергу")

app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle))

print("BOT RUNNING")
app.run_polling()