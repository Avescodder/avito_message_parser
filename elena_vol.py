#ключ доступа клиента от 11:32 09/05/24: UA1IVRK5Qhm6LWEu9iuodgF_qs1Tzk-3JuyTKtWf
#client_id = I6PdLx7Wy21W2Upg6gvt
#client_secret = lO1R355g_yKz5ki3B0_EVYLYU0BN6omV5i1_alyu
import aiohttp
import asyncio
import aiosqlite

client_id = "0j6FFI-Ii1uyp8Nm_4i_"
user_id = "103286876"
client_secret = "uyf8aP2x3wFVg7SKf8_XjBjG2LdZlDcDC-RCX0_x"
api_token = "UA1IVRK5Qhm6LWEu9iuodgF_qs1Tzk-3JuyTKtWf"


async def get_temporary_access_token(client_id, client_secret):
    url = "https://api.avito.ru/token/"
    headers = {
        "Content-Type": "application/x-www-form-urlencoded"
    }
    data = {
        "client_id": client_id,
        "client_secret": client_secret,
        "grant_type": "client_credentials"
    }

    async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=False)) as session:
        async with session.post(url, headers=headers, data=data) as response:
            response.raise_for_status()  # Проверка на успешный ответ
            global api_token
            api_token = (await response.json()).get("access_token")
            print(api_token)
            return api_token


async def get_chat_info(api_token, client_id):
    url = f"https://api.avito.ru/messenger/v2/accounts/{user_id}/chats"
    headers = {
        "messenger": "read",
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_token}"
    }
    data = {
        "user_id": user_id
    }

    async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=False)) as session:
        async with session.get(url, headers=headers, params=data) as response:
            response.raise_for_status()  # Проверка на успешный ответ
            chats_info = await response.json()
            chat_ids = []
            for chat in chats_info["chats"]:  # Обращаемся к значению ключа "chats"
                chat_ids.append(chat['id'])
            print(chat_ids)
            return chat_ids


async def get_messages(api_token, user_id, chat_ids):
    messages_dict = {}
    for chat_id in chat_ids:
        url = f"https://api.avito.ru/messenger/v3/accounts/{user_id}/chats/{chat_id}/messages/"
        headers = {
            "Authorization": f"Bearer {api_token}"
        }

        async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=False)) as session:
            async with session.get(url, headers=headers) as response:
                response.raise_for_status()  # Проверка на успешный ответ
                messages_info = await response.json()
                messages_dict[chat_id] = messages_info
    return messages_dict


async def send_question(api_token, user_id, chat_id, question_number, question_text):
    url = f"https://api.avito.ru/messenger/v1/accounts/{user_id}/chats/{chat_id[0]}/messages"
    headers = {
        "Authorization": f"Bearer {api_token}",
        "Content-Type": "application/json"
    }
    data = {
        "message": {
            "text": f"Вопрос {question_number}: {question_text}"
        },
        "type": "text"
    }

    async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=False)) as session:
        async with session.post(url, headers=headers, json=data) as response:
            response.raise_for_status()  # Проверка на успешный ответ
            print(f"Сообщение с вопросом {question_number} отправлено успешно в чат {chat_id}")
            return True


def process_answer(answer):
    # Здесь вы можете обработать ответ пользователя и выполнить соответствующие действия
    if answer == "1":
        print("Пользователь ответил на первый вопрос")
    elif answer == "2":
        print("Пользователь ответил на второй вопрос")
    else:
        print("Пользователь ответил на другой вопрос")

async def get_chat_messages(api_token, user_id, chat_id, limit=100, offset=0):
    url = f"https://api.avito.ru/messenger/v3/accounts/{user_id}/chats/{chat_id}/messages/"
    headers = {
        "Authorization": f"Bearer {api_token}"
    }
    params = {
        "limit": limit,
        "offset": offset
    }

    async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=False)) as session:
        async with session.get(url, headers=headers, params=params) as response:
            response.raise_for_status()  # Проверка на успешный ответ
            messages_info = await response.json()
            return messages_info
async def save_message_info(db_path, message_id, author_id, chat_id, status="unknown"):
    # Пропускаем запись, если author_id равен нулю
    if author_id == "0" or author_id == 0:
        print("Запись с author_id равным нулю не будет добавлена")
        return

    async with aiosqlite.connect(db_path) as db:
        # Проверяем, существует ли уже запись с таким author_id и chat_id
        async with db.execute("SELECT COUNT(*) FROM dialogs WHERE author_id = ? AND chat_id = ?", (author_id, chat_id)) as cursor:
            count = await cursor.fetchone()
            if count[0] > 0:
                # Запись с таким author_id и chat_id уже существует
                print(f"Запись с author_id {author_id} и chat_id {chat_id} уже существует, запись не будет добавлена.")
                return False
            else:
                # Вставка новой записи с учетом chat_id
                await db.execute("INSERT INTO dialogs (author_id, chat_id, status) VALUES (?, ?, ?)", (author_id, chat_id, status))
                await db.commit()
                print(f"Запись с author_id {author_id} и chat_id {chat_id} успешно добавлена.")
                return True
async def process_and_save_messages(api_token, user_id, chat_id, db_path):
    messages_info = await get_chat_messages(api_token, user_id, chat_id)
    for message in messages_info.get('messages', []):
        message_id = message['id']
        author_id = message['author_id']
        await save_message_info(db_path, message_id, author_id, chat_id)


async def main():
    async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=False)):
        print(await get_temporary_access_token(client_id, client_secret))
        chat_ids = await get_chat_info(api_token, client_id)
        print(chat_ids)
        for chat_id in chat_ids:  # Ensure chat_id is used correctly in the loop
            await process_and_save_messages(api_token, user_id, chat_id, db_path="db_avito.sqlite3")  # Pass each chat_id individually
            
if __name__ == "__main__":
    asyncio.run(main())
