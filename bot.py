import os  # Библиотека для работы с переменными окружения и файлами
import instaloader  # Библиотека для скачивания контента из Instagram
from telegram import Update  # Класс для работы с сообщениями Telegram
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes  # Инструменты для создания бота

# Получаем токен бота из переменной окружения (для безопасности)
TOKEN = os.getenv("TELEGRAM_TOKEN")

# Функция для команды /start — отправляет приветственное сообщение
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Привет! Отправь мне ссылку на видео из Instagram, и я скачаю его для тебя.")

# Функция для обработки текстовых сообщений — проверяет ссылки и скачивает видео
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message_text = update.message.text  # Получаем текст сообщения от пользователя
    if "instagram.com" in message_text:  # Проверяем, есть ли в тексте ссылка на Instagram
        await update.message.reply_text("Скачиваю видео, подожди немного...")  # Сообщаем, что процесс начался
        try:
            # Настраиваем Instaloader для скачивания только видео
            L = instaloader.Instaloader(download_pictures=False, download_videos=True, 
                                        download_video_thumbnails=False, download_geotags=False, 
                                        download_comments=False, save_metadata=False)
            # Извлекаем короткий код поста из ссылки (например, из https://www.instagram.com/p/ABC123/)
            shortcode = message_text.split("/")[-2]
            # Загружаем пост по короткому коду
            post = instaloader.Post.from_shortcode(L.context, shortcode)
            # Скачиваем видео в папку "downloads"
            L.download_post(post, target="downloads")
            # Ищем скачанный видеофайл в папке
            for root, dirs, files in os.walk("downloads"):
                for file in files:
                    if file.endswith(".mp4"):  # Проверяем, что это видео
                        video_path = os.path.join(root, file)  # Получаем путь к файлу
                        # Отправляем видео пользователю
                        with open(video_path, 'rb') as video_file:
                            await update.message.reply_video(video_file)
                        # Удаляем файл после отправки, чтобы не засорять сервер
                        os.remove(video_path)
                        break  # Выходим из цикла после отправки
            await update.message.reply_text("Готово! Видео отправлено.")  # Сообщаем об успехе
        except Exception as e:  # Если что-то пошло не так
            await update.message.reply_text(f"Ошибка: {e}")  # Отправляем сообщение об ошибке
    else:  # Если в сообщении нет ссылки
        await update.message.reply_text("Отправь ссылку на видео из Instagram!")

# Главная функция — запускает бота
def main():
    # Создаём приложение бота с нашим токеном
    application = Application.builder().token(TOKEN).build()
    
    # Добавляем обработчик для команды /start
    application.add_handler(CommandHandler("start", start))
    # Добавляем обработчик для всех текстовых сообщений (кроме команд)
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    # Запускаем бот через вебхук (нужно для Render)
    application.run_webhook(
        listen="0.0.0.0",  # Слушаем все подключения
        port=int(os.environ.get("PORT", 5000)),  # Порт задаётся Render, по умолчанию 5000
        url_path=TOKEN,  # Часть URL для вебхука
        webhook_url=f"https://{os.environ.get('RENDER_EXTERNAL_HOSTNAME')}/{TOKEN}"  # Полный URL вебхука
    )

# Запускаем бота, если файл запущен напрямую
if __name__ == "__main__":
    main()
