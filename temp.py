import os
import asyncio
import sqlite3
import json
from telethon import TelegramClient, events
from telethon.errors import ChannelPrivateError
from dotenv import load_dotenv

# --- Настройки ---
load_dotenv()

API_ID = int(os.getenv("TELEGRAM_API_ID"))
API_HASH = os.getenv("TELEGRAM_API_HASH")
SESSION = os.getenv("TG_SESSION", "vitaliy_session")
TARGET = "@vitaliy_otkrutochkin" 
TO = os.getenv("TELEGRAM_TO")    
MEDIA_DIR = os.getenv("MEDIA_DIR", "media_vitaliy")

os.makedirs(MEDIA_DIR, exist_ok=True)

# --- Инициализация БД ---
conn = sqlite3.connect("vitaliy_posts.db", check_same_thread=False)
cur = conn.cursor()
cur.execute("""
CREATE TABLE IF NOT EXISTS posts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    msg_id INTEGER,
    text TEXT,
    date TEXT,
    media_path TEXT,
    has_media INTEGER,
    raw_json TEXT
)
""")
conn.commit()

# --- Инициализация клиента ---
client = TelegramClient(SESSION, API_ID, API_HASH)

@client.on(events.NewMessage(chats=TARGET))
async def new_post_handler(event):
    msg = event.message
    text = msg.message or ""
    date = msg.date.isoformat()
    has_media = 0
    media_path = None

    # --- Скачиваем медиа ---
    if msg.media:
        has_media = 1
        try:
            filename = f"{msg.id}"
            path = await client.download_media(msg.media, file=os.path.join(MEDIA_DIR, filename))
            media_path = path
            print(f"📸 Медиа сохранено: {path}")
        except Exception as e:
            print("Ошибка скачивания:", e)

    # --- Сохраняем в БД ---
    raw = json.dumps(msg.to_dict(), default=str, ensure_ascii=False)
    cur.execute("""
        INSERT INTO posts (msg_id, text, date, media_path, has_media, raw_json)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (msg.id, text, date, media_path, has_media, raw))
    conn.commit()

    # --- Отправляем уведомление ---
    try:
        if has_media and media_path:
            await client.send_file(TO, media_path, caption=text or "📢 Новый пост!")
        else:
            await client.send_message(TO, f"📢 Новый пост:\n\n{text}")
        print(f"✉️ Уведомление отправлено → {TO}")
    except Exception as e:
        print("⚠️ Ошибка при отправке уведомления:", e)

    print(f"💬 Новая публикация ({msg.id}): {text[:80]!r}")

async def main():
    try:
        await client.start()
        print(f"✅ Парсер запущен. Слушаю канал {TARGET} и пересылаю в {TO}...")
        await client.run_until_disconnected()
    except ChannelPrivateError:
        print("❌ Канал приватный или доступ ограничен. Убедись, что аккаунт подписан на канал.")

if __name__ == "__main__":
    asyncio.run(main())
