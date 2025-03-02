import os
import time
import random
import requests
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# Токен бота из переменной окружения
TOKEN = os.getenv("TELEGRAM_TOKEN")

# Заголовки для маскировки запросов
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Accept-Language": "en-US,en;q=0.9",
}

# Команда /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Привет! Я бот для скачивания видео из Instagram.\n"
        "Отправь мне публичную ссылку на Reels или пост, и я скачаю видео для тебя! 🎥"
    )

# Обработка сообщений со ссылками
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message_text = update.message.text
    if "instagram.com" in message_text:
        await update.message.reply_text("⏳ Проверяю ссылку, подожди немного...")
        try:
            # Извлекаем shortcode из ссылки
            shortcode = message_text.split("/")[-2]
            if not shortcode:
                raise ValueError("Ссылка некорректна, нет shortcode.")

            # Формируем URL для iqsaved.com
            iqsaved_url = f"https://iqsaved.com/ru/download-reels/{shortcode}/"
            
            # Запрос к iqsaved.com
            response = requests.get(iqsaved_url, headers=headers)
            if response.status_code != 200:
                raise Exception(f"Ошибка доступа к iqsaved.com: {response.status_code}")

            # Извлекаем прямую ссылку на видео из ответа (пример парсинга HTML)
            video_url = None
            if "mp4" in response.text:
                # Здесь предполагается, что в HTML есть прямая ссылка на mp4
                # Реальный парсинг зависит от структуры страницы iqsaved.com
                start_idx = response.text.find("https://")
                end_idx = response.text.find(".mp4") + 4
                if start_idx != -1 and end_idx != -1:
                    video_url = response.text[start_idx:end_idx]
            
            if not video_url:
                raise Exception("Не удалось найти ссылку на видео в ответе iqsaved.com")

            # Скачиваем видео
            await update.message.reply_text("📥 Начинаю загрузку...")
            video_response = requests.get(video_url, headers=headers, stream=True)
            if video_response.status_code != 200:
                raise Exception(f"Ошибка загрузки видео: {video_response.status_code}")

            # Сохраняем видео временно
            video_path = f"temp_video_{shortcode}.mp4"
            with open(video_path, "wb") as f:
                for chunk in video_response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)

            # Прогресс-бар
            for i in range(1, 6):
                await update.message.reply_text(f"📥 Загрузка: {i * 20}%")
                time.sleep(1)

            # Отправляем видео в Telegram
            with open(video_path, "rb") as video_file:
                await update.message.reply_video(video_file)
            
            # Удаляем временный файл
            os.remove(video_path)
            
            await update.message.reply_text("✅ Готово! Видео отправлено.")

        except Exception as e:
            await update.message.reply_text(f"❌ Ошибка: {e}")
    else:
        await update.message.reply_text("🔗 Отправь мне ссылку на видео из Instagram!")

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
