import os
import time
import instaloader
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# Получаем токен бота из переменной окружения
TOKEN = os.getenv("TELEGRAM_TOKEN")

# Заголовки для маскировки под браузер
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://www.instagram.com/",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Upgrade-Insecure-Requests": "1",
}

# Команда /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Привет! Я бот для скачивания видео из Instagram.\n"
        "Просто отправь мне ссылку на пост, и я скачаю видео для тебя! 🎥"
    )

# Обработка сообщений со ссылками
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message_text = update.message.text
    if "instagram.com" in message_text:
        await update.message.reply_text("⏳ Скачиваю видео, подожди немного...")
        try:
            # Настройка Instaloader без авторизации
            L = instaloader.Instaloader(
                download_pictures=False,
                download_videos=True,
                download_video_thumbnails=False,
                download_geotags=False,
                download_comments=False,
                save_metadata=False
            )
            # Применяем заголовки для маскировки
            L.context._session.headers.update(headers)
            
            # Извлекаем shortcode из ссылки
            shortcode = message_text.split("/")[-2]
            post = instaloader.Post.from_shortcode(L.context, shortcode)
            
            # Скачиваем пост в папку "downloads"
            L.download_post(post, target="downloads")
            
            # Имитация прогресс-бара
            for i in range(1, 6):
                await update.message.reply_text(f"📥 Загрузка: {i * 20}%")
                time.sleep(1)  # Имитация времени загрузки
            
            # Поиск и отправка видео
            video_path = None
            for root, dirs, files in os.walk("downloads"):
                for file in files:
                    if file.endswith(".mp4"):
                        video_path = os.path.join(root, file)
                        with open(video_path, 'rb') as video_file:
                            await update.message.reply_video(video_file)
                        # Удаляем видео после отправки
                        os.remove(video_path)
                        break
                if video_path:
                    break
            
            if video_path:
                await update.message.reply_text("✅ Готово! Видео отправлено.")
            else:
                await update.message.reply_text("❌ Не удалось найти видео в посте.")
        
        except Exception as e:
            await update.message.reply_text(f"❌ Ошибка: {e}")
    else:
        await update.message.reply_text("🔗 Пожалуйста, отправь мне ссылку на видео из Instagram!")

# Основная функция
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
