import os
import asyncio
import instaloader
import shutil
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes

TOKEN = os.getenv("TELEGRAM_TOKEN")
INSTA_USERNAME = "test85046"
INSTA_PASSWORD = "Testtest1234567890"
SESSION_FILE = "sessionfile"

L = instaloader.Instaloader()

def login_instagram():
    try:
        if os.path.exists(SESSION_FILE):
            L.load_session_from_file(INSTA_USERNAME, SESSION_FILE)
            print("Сессия загружена")
        else:
            print(f"Попытка входа с {INSTA_USERNAME}")
            L.login(INSTA_USERNAME, INSTA_PASSWORD)
            L.save_session_to_file(SESSION_FILE)
            print("Сессия сохранена")
    except Exception as e:
        print(f"Ошибка авторизации: {e}")
        raise

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[InlineKeyboardButton("Скачать видео", callback_data="download"), InlineKeyboardButton("Помощь", callback_data="help")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("👋 Привет! Выбери действие:", reply_markup=reply_markup)

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data == "download":
        await query.edit_message_text("📥 Отправь ссылку на видео:")
    elif query.data == "help":
        await query.edit_message_text("ℹ️ Отправь ссылку на пост или рил. Поддерживаются публичные и приватные видео.")

async def download_video(url, update, context):
    try:
        shortcode = url.split("/")[-2] if url.endswith("/") else url.split("/")[-1].split("?")[0]
        post = instaloader.Post.from_shortcode(L.context, shortcode)
        if not post.is_video:
            raise Exception("Это не видео.")
        
        if os.path.exists("downloads"):
            shutil.rmtree("downloads")
        os.makedirs("downloads")
        
        L.dirname_pattern = "downloads/{shortcode}"
        await update.message.reply_text("⏳ Загрузка началась...")

        async def fake_progress():
            for i in range(0, 101, 20):
                await asyncio.sleep(1)
                await update.message.reply_text(f"📊 Прогресс: {i}%")

        asyncio.create_task(fake_progress())
        L.download_post(post, target="downloads")
        
        video_path = f"downloads/{shortcode}/{shortcode}.mp4"
        if not os.path.exists(video_path):
            raise Exception("Файл не найден.")
        
        with open(video_path, "rb") as video_file:
            await update.message.reply_video(video_file, caption="✅ Готово!")
        
        shutil.rmtree("downloads")
    except Exception as e:
        await update.message.reply_text(f"⚠️ Ошибка: {e}")
        if os.path.exists("downloads"):
            shutil.rmtree("downloads")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if "instagram.com" in update.message.text:
        await download_video(update.message.text, update, context)
    else:
        await update.message.reply_text("❌ Неверная ссылка.")

def main():
    login_instagram()  # Синхронный вызов для авторизации
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    port = int(os.environ.get("PORT", 5000))
    host = "0.0.0.0"
    app.run_webhook(listen=host, port=port, url_path=TOKEN, webhook_url=f"https://{os.environ.get('RENDER_EXTERNAL_HOSTNAME')}/{TOKEN}")

if __name__ == "__main__":
    main()
