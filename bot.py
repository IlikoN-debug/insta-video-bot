import os
import random
import asyncio
import requests
from bs4 import BeautifulSoup
import shutil
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# Токен Telegram из переменной окружения
TOKEN = os.getenv("TELEGRAM_TOKEN")
SAVEFROM_URL = "https://uk.savefrom.net/savefrom.php"

# Функция для команды /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Привет! Отправь мне ссылку на видео из Instagram, и я скачаю его для тебя через SaveFrom.net.")

# Функция для загрузки видео через SaveFrom.net
async def download_video_from_savefrom(url):
    try:
        # Параметры запроса к SaveFrom.net
        payload = {
            "sf_url": url,
            "new": "2",
            "lang": "uk",
            "app": "",
            "country": "ua",
            "os": "Windows",
            "browser": "Chrome",
            "channel": "second"
        }
        
        # Отправляем POST-запрос на SaveFrom.net
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        response = requests.post(SAVEFROM_URL, data=payload, headers=headers)
        response.raise_for_status()

        # Парсим HTML-ответ
        soup = BeautifulSoup(response.text, "html.parser")
        
        # Ищем кнопку "Завантажити MP4" или прямую ссылку на видео
        download_button = soup.select_one("a[href*='mp4']")
        if not download_button:
            raise Exception("Не удалось найти ссылку для скачивания.")

        video_url = download_button["href"]
        
        # Скачиваем видео
        video_response = requests.get(video_url, headers=headers, stream=True)
        video_response.raise_for_status()

        # Сохраняем видео во временный файл
        if os.path.exists("downloads"):
            shutil.rmtree("downloads")
        os.makedirs("downloads")
        
        video_path = "downloads/video.mp4"
        with open(video_path, "wb") as f:
            for chunk in video_response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        return video_path
    
    except Exception as e:
        raise Exception(f"Ошибка при загрузке видео: {str(e)}")

# Функция для обработки текстовых сообщений
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message_text = update.message.text
    
    if "instagram.com" in message_text:
        await update.message.reply_text("Скачиваю видео через SaveFrom.net, подожди немного...")
        
        try:
            # Случайная задержка для имитации человеческого поведения
            await asyncio.sleep(random.uniform(1.0, 3.0))
            
            # Загружаем видео
            video_path = await download_video_from_savefrom(message_text)
            
            # Отправляем видео пользователю
            with open(video_path, 'rb') as video_file:
                await update.message.reply_video(video_file)
            
            # Удаляем временный файл
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
