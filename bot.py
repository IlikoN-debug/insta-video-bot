import os
import asyncio
import instaloader
import shutil
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
from telegram.constants import ParseMode

# Telegram токен
TOKEN = os.getenv("TELEGRAM_TOKEN")

# Instagram логин и пароль
INSTA_USERNAME = "test85046"
INSTA_PASSWORD = "testtest1234567890"

# Создаем экземпляр Instaloader
L = instaloader.Instaloader()

# Функция авторизации в Instagram
async def login_instagram():
    try:
        L.login(INSTA_USERNAME, INSTA_PASSWORD)
        print("Успешно авторизован в Instagram")
    except Exception as e:
        print(f"Ошибка авторизации: {e}")

# Функция для команды /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("Скачать видео", callback_data="download")],
        [InlineKeyboardButton("Помощь", callback_data="help")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "👋 Привет! Я бот для скачивания видео из Instagram.\nВыбери действие:",
        reply_markup=reply_markup
    )

# Функция обработки кнопок
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "download":
        await query.edit_message_text("📥 Отправь мне ссылку на видео из Instagram:")
    elif query.data == "help":
        await query.edit_message_text(
            "ℹ️ Как использовать бота:\n"
            "1. Нажми 'Скачать видео'\n"
            "2. Отправь ссылку на пост или рил\n"
            "3. Дождись загрузки\n\n"
            "Поддерживаются публичные и приватные видео (если аккаунт авторизован)."
        )

# Функция для отслеживания прогресса загрузки
async def progress_callback(update, context, filename, total_size):
    def update_progress(downloaded, total):
        if total > 0:
            percent = int((downloaded / total) * 100)
            context.user_data["last_percent"] = percent
            asyncio.create_task(update.message.reply_text(f"📊 Прогресс: {percent}%"))

    L.download_progress_callback = update_progress

# Функция загрузки видео
async def download_video(url, update, context):
    try:
        # Извлекаем shortcode из URL
        shortcode = url.split("/")[-2] if url.endswith("/") else url.split("/")[-1].split("?")[0]
        
        # Загружаем пост
        post = instaloader.Post.from_shortcode(L.context, shortcode)
        
        # Проверяем, есть ли видео
        if not post.is_video:
            raise Exception("Это не видео.")

        # Создаем папку downloads
        if os.path.exists("downloads"):
            shutil.rmtree("downloads")
        os.makedirs("downloads")

        # Устанавливаем путь для сохранения
        L.dirname_pattern = "downloads/{shortcode}"
        await update.message.reply_text("⏳ Начинаю загрузку...")

        # Отслеживание прогресса
        await progress_callback(update, context, f"{shortcode}.mp4", post.video_duration * 1024 * 1024)  # Примерный размер
        
        # Загружаем видео
        L.download_post(post, target="downloads")
        
        # Ищем видео файл
        video_path = f"downloads/{shortcode}/{shortcode}.mp4"
        if not os.path.exists(video_path):
            raise Exception("Файл видео не найден.")

        # Отправляем видео
        with open(video_path, "rb") as video_file:
            await update.message.reply_video(video_file, caption="✅ Видео загружено!")
        
        # Удаляем папку после отправки
        shutil.rmtree("downloads")
        
    except Exception as e:
        await update.message.reply_text(f"⚠️ Ошибка: {str(e)}")
        if os.path.exists("downloads"):
            shutil.rmtree("downloads")

# Функция обработки текстовых сообщений
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message_text = update.message.text
    
    if "instagram.com" in message_text:
        await download_video(message_text, update, context)
    else:
        await update.message.reply_text("❌ Это не похоже на ссылку Instagram. Отправь корректную ссылку.")

# Главная функция
def main():
    # Авторизация в Instagram при старте
    asyncio.run(login_instagram())
    
    # Настройка бота
    application = Application.builder().token(TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button_handler))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    # Настройки для Render
    port = int(os.environ.get("PORT", 5000))
    host = "0.0.0.0"
    
    application.run_webhook(
        listen=host,
        port=port,
        url_path=TOKEN,
        webhook_url=f"https://{os.environ.get('RENDER_EXTERNAL_HOSTNAME')}/{TOKEN}"
    )

if __name__ == "__main__":
    main()
