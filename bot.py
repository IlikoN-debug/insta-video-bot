import os
import random
import asyncio
import requests
from bs4 import BeautifulSoup
import shutil
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

TOKEN = os.getenv("TELEGRAM_TOKEN")
SAVEFROM_URL = "https://uk.savefrom.net/savefrom.php"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Привет! Отправь мне ссылку на видео из Instagram, и я скачаю его для тебя через SaveFrom.net.")

async def download_video_from_savefrom(url, update, context):
    try:
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
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/91.0.4472.124"
        }
        response = requests.post(SAVEFROM_URL, data=payload, headers=headers)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")
        download_link = soup.find("a", class_="def-btn", href=True) or soup.find("a", href=lambda x: x and "mp4" in x.lower())
        if not download_link:
            # Логируем первые 4000 символов ответа в чат
            await context.bot.send_message(chat_id=update.effective_chat.id, text=f"HTML ответа SaveFrom.net:\n{response.text[:4000]}")
            raise Exception("Не удалось найти ссылку для скачивания.")

        video_url = download_link["href"]
        video_response = requests.get(video_url, headers=headers, stream=True)
        video_response.raise_for_status()

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

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message_text = update.message.text
    
    if "instagram.com" in message_text:
        await update.message.reply_text("Скачиваю видео через SaveFrom.net, подожди немного...")
        
        try:
            await asyncio.sleep(random.uniform(1.0, 3.0))
            video_path = await download_video_from_savefrom(message_text, update, context)
            
            with open(video_path, 'rb') as video_file:
                await update.message.reply_video(video_file)
            
            os.remove(video_path)
            await update.message.reply_text("✅ Видео успешно отправлено!")
            
        except Exception as e:
            error_msg = f"⚠️ Ошибка: {str(e)}"
            await update.message.reply_text(error_msg)
            
    else:
        await update.message.reply_text("❌ Это не похоже на ссылку Instagram. Попробуй еще раз!")

def main():
    application = Application.builder().token(TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
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
