import os
import instaloader
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

TOKEN = os.getenv("TELEGRAM_TOKEN")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Привет! Отправь мне ссылку на видео из Instagram, и я скачаю его для тебя.")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message_text = update.message.text
    if "instagram.com" in message_text:
        await update.message.reply_text("Скачиваю видео, подожди немного...")
        try:
            # Настраиваем Instaloader с User-Agent для обхода блокировок
            L = instaloader.Instaloader(download_pictures=False, download_videos=True, 
                                        download_video_thumbnails=False, download_geotags=False, 
                                        download_comments=False, save_metadata=False)
            L.context._session.headers.update({'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'})
            # Извлекаем короткий код поста
            shortcode = message_text.split("/")[-2]
            # Загружаем пост
            post = instaloader.Post.from_shortcode(L.context, shortcode)
            L.download_post(post, target="downloads")
            # Ищем видео в папке
            for root, dirs, files in os.walk("downloads"):
                for file in files:
                    if file.endswith(".mp4"):
                        video_path = os.path.join(root, file)
                        with open(video_path, 'rb') as video_file:
                            await update.message.reply_video(video_file)
                        os.remove(video_path)
                        break
            await update.message.reply_text("Готово! Видео отправлено.")
        except Exception as e:
            await update.message.reply_text(f"Ошибка: {e}")
    else:
        await update.message.reply_text("Отправь ссылку на видео из Instagram!")

def main():
    application = Application.builder().token(TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.run_webhook(
        listen="0.0.0.0",
        port=int(os.environ.get("PORT", 5000)),
        url_path=TOKEN,
        webhook_url=f"https://{os.environ.get('RENDER_EXTERNAL_HOSTNAME')}/{TOKEN}"
    )

if __name__ == "__main__":
    main()
