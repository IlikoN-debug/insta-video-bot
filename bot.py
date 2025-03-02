async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message_text = update.message.text
    if "instagram.com" in message_text:
        logger.info(f"Получена ссылка: {message_text}")
        await update.message.reply_text("⏳ Проверяю...")

        try:
            # POST-запрос
            data = {"url": message_text}
            response = requests.post("https://iqsaved.com/ru/", headers=headers, data=data)
            logger.info(f"Ответ: {response.status_code}")
            if response.status_code != 200:
                raise Exception(f"Ошибка: {response.status_code}")

            # Парсинг кнопки
            soup = BeautifulSoup(response.text, "html.parser")
            download_button = soup.find("a", class_="button button__blue")
            if not download_button or not download_button.get("href"):
                logger.error("Кнопка не найдена")
                raise Exception("Кнопка 'Скачать' не найдена")
            video_url = download_button["href"]
            logger.info(f"Ссылка на видео: {video_url}")

            # Скачивание
            await update.message.reply_text("📥 Загрузка...")
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
