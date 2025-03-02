import os
import time
import random
import requests
import logging
from bs4 import BeautifulSoup
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# Настройка логов
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Токен бота
TOKEN = os.getenv("TELEGRAM_TOKEN")

# Заголовки для запросов
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/91.0.4472.124",
    "Content-Type": "application/x-www-form-urlencoded",
}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 Привет! Отправь ссылку на Reels, и я скачаю видео!")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message_text = update.message.text
    if "instagram.com" in message_text:
        logger.info(f"Получена ссылка: {message_text}")
        await update.message.reply_text("⏳ Проверяю...")

        try:
            # Первый POST-запрос
            data = {"url": message_text}
            response = requests.post("https://iqsaved.com/ru/", headers=headers, data=data)
            logger.info(f"Первый ответ: {response.status_code}")
            if response.status_code != 200:
                raise Exception(f"Ошибка: {response.status_code}")

            # Парсинг кнопки "Скачать"
            soup = BeautifulSoup(response.text, "html.parser")
            download_button = soup.find("a", class_="button button__blue")
            if not download_button or not download_button.get("href"):
                logger.error("Кнопка не найдена")
                raise Exception("Кнопка 'Скачать' не найдена")
            video_url = download_button["href"]
            logger.info(f"Ссылка на видео: {video_url}")

            # Скачивание
            await update.message.reply_text("📥 Начинаю загрузку...")
            video_response = requests.get(video_url, headers=headers, stream=True)
            if video_response.status_code != 200:
                logger.error(f"Ошибка загрузки: {video_response.status_code}")
                raise Exception(f"Ошибка загрузки: {video_response.status_code}")
            
            video_path = "temp_video.mp4"
            with open(video_path, "wb") as f:
                for chunk in video_response.iter_content(8192):
                    f.write(chunk)

            # Прогресс-бар
            for i in range(1, 6):
                await update.message.reply_text(f"📥 {i * 20}%")
                time.sleep(0.5)

            # Отправка и удаление
            logger.info("Отправляю видео в Telegram")
            with open(video_path, "rb") as video_file:
                await update.message.reply_video(video_file)
            os.remove(video_path)
            logger.info("Файл удалён")
            await update.message.reply_text("✅ Готово!")

        except Exception as e:
            logger.error(f"Ошибка: {str(e)}")
            await update.message.reply_text(f"❌ Ошибка: {e}")
    else:
        await update.message.reply_text("🔗 Отправь ссылку на Instagram!")

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
