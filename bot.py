import os
import random
import asyncio
import yt_dlp
import shutil
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

TOKEN = os.getenv("TELEGRAM_TOKEN")

# Функция для команды /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Привет! Отправь мне ссылку на видео из Instagram, и я скачаю его для тебя.")

# Функция для обработки текстовых сообщений
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message_text = update.message.text
    
    if "instagram.com" in message_text:
        await update.message.reply_text("Скачиваю видео, подожди немного...")
        
        try:
            # Случайная задержка для имитации человеческого поведения
            await asyncio.sleep(random.uniform(1.0, 3.0))
            
            # Настройки для yt-dlp
            ydl_opts = {
                'outtmpl': 'downloads/%(id)s.%(ext)s',  # Сохраняем видео в папку downloads
                'quiet': True,  # Отключаем лишние сообщения
                'no_warnings': True,  # Игнорируем предупреждения
                'format': 'best',  # Скачиваем лучшее качество
            }
            
            # Очистка папки downloads перед загрузкой
            if os.path.exists("downloads"):
                shutil.rmtree("downloads")
            os.makedirs("downloads")
            
            # Скачивание видео
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(message_text, download=True)
                video_path = ydl.prepare_filename(info)
                
            # Отправка видео пользователю
            with open(video_path, 'rb') as video_file:
                await update.message.reply_video(video_file)
            
            # Удаление видео после отправки
            os.remove(video_path)
            await update.message.reply_text("✅ Видео успешно отправлено!")
            
        except Exception as e:
            error_msg = f"⚠️ Ошибка: {str(e)}"
            await update.message.reply_text(error_msg)
            
    else:
        await update.message.reply_text("❌ Это не похоже на ссылку Instagram. Попробуй еще раз!")

# Главная функция
def main():
    application = Application.builder().token(TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    # Указываем порт и хост для Render
    port = int(os.environ.get("PORT", 5000))
    host = "0.0.0.0"  # Используем 0.0.0.0 для Render
    
    # Запуск вебхука
    application.run_webhook(
        listen=host,
        port=port,
        url_path=TOKEN,
        webhook_url=f"https://{os.environ.get('RENDER_EXTERNAL_HOSTNAME')}/{TOKEN}"
    )

if __name__ == "__main__":
    main()
