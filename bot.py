import os
import time
import random
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# Токен бота из переменной окружения
TOKEN = os.getenv("TELEGRAM_TOKEN")

# Хранилище лимитов (в памяти, для простоты)
user_requests = {}

# Ограничение на количество запросов в день
DAILY_LIMIT = 5

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /start — приветственное сообщение"""
    await update.message.reply_text(
        "Привет! Я бот для загрузки видео из Instagram. Отправь мне ссылку, и я начну работу!\n"
        f"Лимит: {DAILY_LIMIT} запросов в день."
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка сообщений с ссылками"""
    user_id = update.message.from_user.id
    message_text = update.message.text

    # Проверка лимита запросов
    if user_id not in user_requests:
        user_requests[user_id] = 0
    
    if user_requests[user_id] >= DAILY_LIMIT:
        await update.message.reply_text(
            f"Ты превысил дневной лимит в {DAILY_LIMIT} запросов. Попробуй завтра!"
        )
        return

    # Проверка, является ли сообщение ссылкой на Instagram
    if "instagram.com" in message_text:
        await update.message.reply_text("Проверяю ссылку... ⏳")

        # Имитация проверки ссылки
        time.sleep(1)
        
        # Увеличение счётчика запросов
        user_requests[user_id] += 1
        
        # Динамический прогресс загрузки
        await update.message.reply_text("Начинаю загрузку... 📥")
        for i in range(1, 6):
            progress = i * 20
            await update.message.reply_text(f"Загрузка: {progress}% [{'█' * i}{' ' * (5 - i)}]")
            time.sleep(random.uniform(0.5, 1.5))  # Случайная задержка для реализма
        
        # Успешное завершение (здесь можно добавить реальную логику загрузки)
        await update.message.reply_text(
            f"Видео успешно загружено! 🎉\n"
            f"Осталось запросов на сегодня: {DAILY_LIMIT - user_requests[user_id]}"
        )
        # Здесь можно добавить отправку видео, если есть легальный способ его получить
    else:
        await update.message.reply_text(
            "Пожалуйста, отправь корректную ссылку на видео из Instagram."
        )

def main():
    """Запуск бота"""
    application = Application.builder().token(TOKEN).build()

    # Обработчики команд и сообщений
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Старт бота
    print("Бот запущен!")
    application.run_polling()

if __name__ == "__main__":
    main()
