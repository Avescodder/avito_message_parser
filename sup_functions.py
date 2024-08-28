import aiosqlite
import aiohttp
from aiohttp import web
import asyncio
import json


db_path="db_avito.sqlite3"

# async def is_new_chat(message_data):
#     if message_data.get('payload') and message_data.get('payload').get('type') == 'message':
#         message_information = message_data.get('payload')
#         chat_id = message_information['value'].get('chat_id')
#         # async with 

# db_path = "db_avito.sqlite3"

async def check_chat_and_get_status(chat_id, author_id, api_token, user_id, text):
    async with aiosqlite.connect(db_path) as db:
        cursor = await db.execute("SELECT status FROM dialogs WHERE chat_id = ? AND author_id = ?", (chat_id, author_id))
        row = await cursor.fetchone()
        await cursor.close()
        if row:
            return await process_message(chat_id, author_id, row[0], text, api_token, user_id)
        else:
            return await add_new_chat(chat_id, author_id, api_token, user_id)

async def add_new_chat(chat_id, author_id, api_token, user_id):
    async with aiosqlite.connect(db_path) as db:
        await db.execute("INSERT INTO dialogs (chat_id, author_id, status) VALUES (?, ?, ?)", (chat_id, author_id, 1))
        await db.commit()
    return await send_message(chat_id, messages_dict.get(1, "Спасибо за ваш ответ"), api_token, user_id)

async def send_message(chat_id, message, api_token, user_id):
    api_url = f"https://api.avito.ru/messenger/v1/accounts/{user_id}/chats/{chat_id}/messages"

    headers = {
        "Authorization": f"Bearer {api_token}",
        "Content-Type": "application/json"
    }
    data = {
        "message": {
            "text": f"{message}"
        },
        "type": "text"
    }
    
    async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=False)) as session:
        async with session.post(api_url, headers=headers, json=data) as response:
            response.raise_for_status()
            if response.status == 200:
                print("Сообщение отправлено")
            else:
                print("Ошибка при отправке сообщения")

async def process_message(chat_id, author_id, status, text, api_token, user_id):
    if status == 1:
        new_status = 2 if text!= "1" else print("закидываем в амо")  
        async with aiosqlite.connect(db_path) as db:
            await db.execute("UPDATE dialogs SET status =? WHERE chat_id =? AND author_id =?", (new_status, chat_id, author_id))
            await db.commit()
        await send_message(chat_id, messages_dict.get(status, "Спасибо за ваш ответ!"), api_token, user_id)
    elif status == 2:
        new_status = 3 if text != "1" else print("закидываем в амо")  
        async with aiosqlite.connect(db_path) as db:
            await db.execute("UPDATE dialogs SET status = ? WHERE chat_id = ? AND author_id = ?", (new_status, chat_id, author_id))
            await db.commit()
        await send_message(chat_id, messages_dict.get(status, "Спасибо за ваш ответ!"), api_token, user_id)
    elif status == 3:
        new_status = 4 if text!= "1" else print("закидываем в амо")
        async with aiosqlite.connect(db_path) as db:
            await db.execute("UPDATE dialogs SET status =? WHERE chat_id =? AND author_id =?", (new_status, chat_id, author_id))
            await db.commit()
        await send_message(chat_id, messages_dict.get(status, "Спасибо за ваш ответ!"), api_token, user_id)
    elif status == 4:
        new_status = 5 if text!= "1" else print("закидываем в амо")
        async with aiosqlite.connect(db_path) as db:
            await db.execute("UPDATE dialogs SET status =? WHERE chat_id =? AND author_id =?", (new_status, chat_id, author_id))
            await db.commit()
        await send_message(chat_id, messages_dict.get(status, "Спасибо за ваш ответ!"), api_token, user_id)
    elif status == 5:
        new_status = 6 if text!= "1" else print("закидываем в амо")
        async with aiosqlite.connect(db_path) as db:
            await db.execute("UPDATE dialogs SET status =? WHERE chat_id =? AND author_id =?", (new_status, chat_id, author_id))
            await db.commit()
        print("закидываем в неактивные лиды")
    else:
        print("Братан, эта херь не работает, оно того не стоит, просто забей")
        

messages_dict = {
    1: "Ваше первое сообщение",
    2: "Ваше второе сообщение",
    3: "Ваше третье сообщение",
    4: "Ваше четвертое сообщение",
}
