import os
import instaloader
import random
import time
import shutil
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

TOKEN = os.getenv("TELEGRAM_TOKEN")

# Генератор реалистичных User-Agent (обновлённый список)
USER_AGENTS = [
    "Mozilla/5.0 (iPhone14,3; U; CPU iPhone OS 15_0 like Mac OS X) AppleWebKit/602.1.50 (KHTML, like Gecko) Version/10.0 Mobile/19A346 Safari/602.1",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Linux; Android 13; SM-S901B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Mobile Safari/537.36",
    "Instagram 277.0.0.0.219 Android (33/13; 480dpi; 1080x2400; samsung; SM-M115F; m11q; exynos9611; en_US; 438397864)"
]

# Новые параметры для Instaloader (маскировка под мобильное приложение)
INSTA_SETTINGS = {
    'download_pictures': False,
    'download_videos': True,
    'download_video_thumbnails': False,
    'download_geotags': False,
    'download_comments': False,
    'save_metadata': False,
    'compress_json': False,
    'post_metadata_txt_pattern': "",
    'max_connection_attempts': 2,
    'request_timeout': 10.0,
    'sleep': True
}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Привет! Отправь мне ссылку на видео из Instagram, и я скачаю его для тебя.")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message_text = update.message.text
    
    if "instagram.com" in message_text:
        await update.message.reply_text("Скачиваю видео, подожди немного...")
        
        try:
            # Случайная задержка 1-4 сек для имитации человека
            await asyncio.sleep(random.uniform(1.0, 4.0))
            
            # Генерация случайного User-Agent для каждого запроса
            user_agent = random.choice(USER_AGENTS)
            
            # Инициализация Instaloader с настройками
            L = instaloader.Instaloader(
                user_agent=user_agent,
                **INSTA_SETTINGS
            )
            
            # Очистка предыдущих загрузок
            if os.path.exists("downloads"):
                shutil.rmtree("downloads")
            os.makedirs("downloads")
            
            shortcode = message_text.split("/")[-2]
            post = instaloader.Post.from_shortcode(L.context, shortcode)
            
            # Проверка наличия видео
            if not post.is_video:
                await update.message.reply_text("В посте нет видео!")
                return
                
            L.download_post(post, target="downloads")
            
            # Новый способ поиска видео (более надёжный)
            video_dir = os.path.join("downloads", f"{post.shortcode}")
            video_file = next((f for f in os.listdir(video_dir) if f.endswith(".mp4")), None)
            
            if video_file:
                video_path = os.path.join(video_dir, video_file)
                with open(video_path, 'rb') as video_file:
                    await update.message.reply_video(video_file)
                shutil.rmtree(video_dir)
                await update.message.reply_text("Готово! Видео отправлено.")
            else:
                await update.message.reply_text("Не удалось найти видео")
                
        except Exception as e:
            error_msg = f"Ошибка: {str(e)}"
            # Маскировка технических ошибок для пользователя
            if "Login required" in error_msg:
                error_msg = "Instagram требует авторизации для этого контента"
            await update.message.reply_text(error_msg)
            
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
