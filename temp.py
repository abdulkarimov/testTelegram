import re
import requests
import random
from urllib.parse import unquote
from telethon import TelegramClient
from dotenv import load_dotenv
import os
from PIL import Image

load_dotenv()

api_id = int(os.getenv("TELEGRAM_API_ID"))
api_hash = os.getenv("TELEGRAM_API_HASH")
to = os.getenv("TELEGRAM_TO")

client = TelegramClient("session_name", api_id, api_hash)

async def main():
    message = "С добрым утром 🌞"

    try:
        # пробуем скачать случайную картинку
        q = "открытки с добрым утром и хорошего дня"
        url = "https://yandex.kz/images/search"
        params = {"text": q}
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }

        resp = requests.get(url, params=params, headers=headers, timeout=15)
        html = resp.text
        matches = re.findall(r'img_url=([^&"\']+)', html)

        if not matches:
            raise Exception("Картинок не найдено")

        img_url = unquote(random.choice(matches))
        print("Выбран случайный URL:", img_url)

        r = requests.get(img_url, headers=headers, stream=True, timeout=20)
        file_path = "random_image.jpg"
        with open(file_path, "wb") as f:
            for chunk in r.iter_content(1024):
                f.write(chunk)
        print("Сохранено как", file_path)

        # пересохраняем через Pillow для гарантии
        img = Image.open(file_path).convert("RGB")
        img.save(file_path, "JPEG")
        print("Пересохранено в корректный JPEG")

        await client.send_file(to, file=file_path, caption=message)
        print("✅ Отправлено")
    except Exception as e:
        print("Ошибка при обработке картинки:", e)
        await client.send_message(to, message + " (без картинки)")
        print("✅ Отправлено только сообщение")


with client:
    client.loop.run_until_complete(main())
