import aiohttp
import asyncio
import aiosqlite

client_id = "0j6FFI-Ii1uyp8Nm_4i_"
user_id = "103286876"
client_secret = "uyf8aP2x3wFVg7SKf8_XjBjG2LdZlDcDC-RCX0_x"
db_path="db_avito.sqlite3"

#получение токена
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
        
#получение информации о чатах, chat_ids
async def get_chat_info(api_token, client_id):
    url = f"https://api.avito.ru/messenger/v2/accounts/{user_id}/chats"
    headers = {
        "messenger": "read",
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_token}"
    }
    data = {
        "user_id": user_id,
        "unread_only": "true",
    }

    async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=False)) as session:
        async with session.get(url, headers=headers, params=data) as response:
            response.raise_for_status()  
            chats_info = await response.json()
            chat_ids = []
            for chat in chats_info["chats"]:  
                chat_ids.append(chat['id'])
            print(chat_ids)
            return chat_ids
        
#получение сообщений
async def get_chat_messages(api_token, user_id, chat_id, limit=1, offset=0):
    url = f"https://api.avito.ru/messenger/v3/accounts/{user_id}/chats/{chat_id}/messages/"
    headers = {
        "Authorization": f"Bearer {api_token}"
    }
    params = {
        "limit": limit,
        "offset": offset,
        "unread_only": "true",
    }

    async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=False)) as session:
        async with session.get(url, headers=headers, params=params) as response:
            response.raise_for_status()  # Проверка на успешный ответ
            messages_info = await response.json()
            return messages_info
async def mark_chat_as_read(api_token, user_id, chat_id):
    url = f"https://api.avito.ru/messenger/v1/accounts/{user_id}/chats/{chat_id}/read"
    headers = {
        "Authorization": f"Bearer {api_token}"
    }

    async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=False)) as session:
        async with session.post(url, headers=headers) as response:
            if response.status == 200:
                print("Чат успешно помечен как прочитанный")
                response_data = await response.json()
                print(response_data)  # Выводим ответ сервера для отладки
            else:
                print(f"Ошибка при пометке чата как прочитанного: {response.status}")
#получение информации о id чатов и users_id
async def reg_process_and_save_messages(api_token, user_id, chat_id, db_path):
    messages_info = await get_chat_messages(api_token, user_id, chat_id)
    for message in messages_info.get('messages', []):
        message_id = message['id']
        author_id = message['author_id']
        status = 1
        reason = "TEST"
        await save_message_info(db_path, message_id, author_id, chat_id, status, reason)

#сохранение информации о сообщениях в базу данных
async def save_message_info(db_path, message_id, author_id, chat_id, status, reason):
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
                await db.execute("INSERT INTO dialogs (author_id, chat_id, status, reason) VALUES (?,?,?,?)", (author_id, chat_id, status, reason))
                await db.commit()
                print(f"Запись с author_id {author_id} и chat_id {chat_id} успешно добавлена.")
                return True
#извлечение записей из базы данных для отправки сообщений
async def fetch_messages_with_status_12(db_path):
    async with aiosqlite.connect(db_path) as db:
        async with db.execute("SELECT chat_id FROM dialogs WHERE status = 2 AND author_id != ?", (103286876,)) as cursor:
            return await cursor.fetchall()
        
#отправка сообщения
async def send_message_to_chat(api_token, user_id, chat_id, message, status):
    url = f"https://api.avito.ru/messenger/v1/accounts/{user_id}/chats/{chat_id[0]}/messages"
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
        async with session.post(url, headers=headers, json=data) as response:
            response.raise_for_status()  # Проверка на успешный ответ
            message_response = await response.json()  # Получаем JSON ответ
            print(message_response)  # Выводим JSON ответ на экран
            last_message_id = message_response.get('id')  # Извлекаем ID сообщения
            print(f"Сообщение с вопросом {message} отправлено успешно в чат {chat_id}, ID сообщения: {last_message_id}")
            if status == 1:
                return await monitor_chat_responses(api_token, user_id, chat_id, last_message_id, message_text = message)
            elif status == 2:
                return await monitor_chat_responses_second_quest(api_token, user_id, chat_id, last_message_id, message_text = message)
            elif status == 3:
                return await monitor_chat_responses_third_quest(api_token, user_id, chat_id, last_message_id, message_text = message)
            elif status == 4:
                return await monitor_chat_responses_fourth_quest(api_token, user_id, chat_id, last_message_id, message_text = message)
            


async def monitor_chat_responses(api_token, user_id, chat_id, last_message_id, message_text):
    async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=False)):
        while True:
            await asyncio.sleep(30)  # Пауза на 30 секунд перед следующей проверкой
            print(f"Мониторинг чата {chat_id}")
            messages_info = await get_chat_messages(api_token, user_id, chat_id[0])
            for message in messages_info.get('messages', []):

                if message['id'] > last_message_id and message['author_id'] != user_id and message.get('content', {}).get('text') != message_text:
                    await mark_chat_as_read(api_token, user_id, chat_id[0])
                    print(message["id"], message["author_id"])  # Проверяем, что это новое сообщение от пользователя
                    message_content = message.get('content', {})
                    user_response = message_content.get('text', 'Сообщение не содержит текста')
                    last_message_id = message['id']
                    print(f"Новое сообщение от пользователя: {user_response}")
                    if user_response == "1":
                        print("Ответ пользователя равен одному. Завершаем программу.")
                        return  # Завершаем мониторинг
                    elif user_response in ["2", "3", "4"]:
                        print(f"Ответ пользователя {user_response}. Вызываем другую функцию.")
                        new_question = "Вопрос номер два"
                        await update_status_and_ask_question(api_token, user_id, chat_id, db_path, new_question)  # Предполагаемая функция для обработки
                        return  # Завершаем мониторинг после обработки
                    else:
                        print("Ответ пользователя не соответствует ожидаемым значениям. Просим ответить правильно.")
                        await send_message_to_chat(api_token, user_id, chat_id, "Пожалуйста, ответьте на сообщение в правильном формате.", status=1)
                        last_message_id = message['id']  # Обновляем ID последнего сообщения для продолжения мониторинга
                        continue  # Продолжаем мониторинг чата
                else:
                    print(f"Сообщение с ID {message['id']} не является новым.")
# Обновление статуса в базе данных и отправка нового вопроса
async def update_status_and_ask_question(api_token, user_id, chat_id, db_path, new_question):
    # Обновляем статус в базе данных на 2
    async with aiosqlite.connect(db_path) as db:
        # Исправленный вызов, предполагая, что chat_id уже является кортежем
        await db.execute("UPDATE dialogs SET status = 2 WHERE chat_id = ?", chat_id)
        await db.commit()
        print(f"Статус для чата {chat_id} обновлён на 2.")

    # Отправляем новый вопрос в чат
    await send_message_to_chat(api_token, user_id, chat_id, new_question, status = 2)

# Измените функцию monitor_chat_responses, чтобы она могла вызывать update_status_and_ask_question
# в зависимости от ответа пользователя
async def monitor_chat_responses_second_quest(api_token, user_id, chat_id, last_message_id, message_text):
    async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=False)):
        while True:
            await asyncio.sleep(30)  # Пауза на 30 секунд перед следующей проверкой
            print(f"Мониторинг чата {chat_id}")
            print(user_id)
            messages_info = await get_chat_messages(api_token, user_id, chat_id[0])
            print(messages_info)
            for message in messages_info.get('messages', []):

                if message['id'] > last_message_id and message['author_id'] != user_id and message.get('content', {}).get('text') != message_text:
                    await mark_chat_as_read(api_token, user_id, chat_id[0])
                    print(message["id"], message["author_id"])  # Проверяем, что это новое сообщение от пользователя
                    message_content = message.get('content', {})
                    user_response = message_content.get('text', 'Сообщение не содержит текста')
                    last_message_id = message['id']
                    print(f"Новое сообщение от пользователя: {user_response}")
                    if user_response == "1":
                        print("Ответ пользователя равен одному. Заливаем в Амо срм.")
                        return
                    # Добавьте обработку других ответов пользователя здесь, если необходимо
                    elif user_response in ["2", "3", "4"]:
                        print(f"Ответ пользователя {user_response}. Вызываем другую функцию.")
                        new_question = "Вопрос номер три"
                        await update_status_ask_question_three(api_token, user_id, chat_id, db_path, new_question)
                        return  # Завершаем мониторинг после обновления статуса и отправки нового вопроса
                    else:
                        print("Ответ пользователя не соответствует ожидаемым значениям. Просим ответить правильно.")
                        await send_message_to_chat(api_token, user_id, chat_id, "Пожалуйста, ответьте на сообщение в правильном формате.", status=2)
                        last_message_id = message['id']  # Обновляем ID последнего сообщения для продолжения мониторинга
                        continue

async def update_status_ask_question_three(api_token, user_id, chat_id, db_path, new_question):
    # Обновляем статус в базе данных на 3
    async with aiosqlite.connect(db_path) as db:
        # Исправленный вызов, предполагая, что chat_id уже является кортежем
        await db.execute("UPDATE dialogs SET status = 3 WHERE chat_id =?", chat_id)
        await db.commit()
        print(f"Статус для чата {chat_id} обновлён на 3.")
    await send_message_to_chat(api_token, user_id, chat_id, new_question, status = 3)

async def monitor_chat_responses_third_quest(api_token, user_id, chat_id, last_message_id, message_text):
    async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=False)):
        while True:
            await asyncio.sleep(30)  # Пауза на 30 секунд перед следующей проверкой
            print(user_id)
            messages_info = await get_chat_messages(api_token, user_id, chat_id[0])
            print(messages_info)
            for message in messages_info.get('messages', []):

                if message['id'] > last_message_id and message['author_id'] != user_id and message.get('content', {}).get('text') != message_text:
                    await mark_chat_as_read(api_token, user_id, chat_id[0])
                    print(message["id"], message["author_id"])  # Проверяем, что это новое сообщение от пользователя
                    message_content = message.get('content', {})
                    user_response = message_content.get('text', 'Сообщение не содержит текста')
                    last_message_id = message['id']
                    print(f"Новое сообщение от пользователя: {user_response}")
                    if user_response == "1":
                        print("Ответ пользователя равен одному. Заливаем в Амо срм.")
                        return
                    # Добавьте обработку других ответов пользователя здесь, если необходимо
                    elif user_response in ["2", "3", "4"]:
                        print(f"Ответ пользователя {user_response}. Вызываем другую функцию.")
                        new_question = "Вопрос номер четыре"
                        await update_status_ask_question_four(api_token, user_id, chat_id, db_path, new_question)
                        return  # Завершаем мониторинг после обновления статуса и отправки нового вопроса
                    else:
                        print("Ответ пользователя не соответствует ожидаемым значениям. Просим ответить правильно.")
                        await send_message_to_chat(api_token, user_id, chat_id, "Пожалуйста, ответьте на сообщение в правильном формате.", status=3)
                        last_message_id = message['id']  # Обновляем ID последнего сообщения для продолжения мониторинга
                        continue

async def update_status_ask_question_four(api_token, user_id, chat_id, db_path, new_question):
    # Обновляем статус в базе данных на 4
    async with aiosqlite.connect(db_path) as db:
        # Исправленный вызов, предполагая, что chat_id уже является кортежем
        await db.execute("UPDATE dialogs SET status = 4 WHERE chat_id =?", chat_id)
        await db.commit()
        print(f"Статус для чата {chat_id} обновлён на 4.")
    await send_message_to_chat(api_token, user_id, chat_id, new_question, status = 4)

async def monitor_chat_responses_fourth_quest(api_token, user_id, chat_id, last_message_id, message_text):
    async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=False)):
        while True:
            await asyncio.sleep(30)  # Пауза на 30 секунд перед следующей проверкой
            print(user_id)
            messages_info = await get_chat_messages(api_token, user_id, chat_id[0])
            print(messages_info)
            for message in messages_info.get('messages', []):

                if message['id'] > last_message_id and message['author_id'] != user_id and message.get('content', {}).get('text') != message_text:
                    await mark_chat_as_read(api_token, user_id, chat_id[0])
                    print(message["id"], message["author_id"])  # Проверяем, что это новое сообщение от пользователя
                    message_content = message.get('content', {})
                    user_response = message_content.get('text', 'Сообщение не содержит текста')
                    last_message_id = message['id']
                    print(f"Новое сообщение от пользователя: {user_response}")
                    if user_response == "1":
                        print("Ответ пользователя равен одному. Заливаем в Амо срм.")
                        return
                    # Добавьте обработку других ответов пользователя здесь, если необходимо
                    elif user_response in ["2", "3", "4"]:
                        print(f"Ответ пользователя {user_response}. Загружаем его в неактивные лиды")
                        return  # Завершаем мониторинг после обновления статуса и отправки нового вопроса
                    else:
                        print("Ответ пользователя не соответствует ожидаемым значениям. Просим ответить правильно.")
                        await send_message_to_chat(api_token, user_id, chat_id, "Пожалуйста, ответьте на сообщение в правильном формате.", status=4)
                        last_message_id = message['id']  # Обновляем ID последнего сообщения для продолжения мониторинга
                        continue
async def main():
    async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=False)):
        api_token = await get_temporary_access_token(client_id, client_secret)
        chat_ids = await get_chat_info(api_token, client_id)
        for chat_id in chat_ids:
            print("uhfisurf")
            await reg_process_and_save_messages(api_token, user_id, chat_id, db_path)
            await mark_chat_as_read(api_token, user_id, chat_id)
        messages_to_send = await fetch_messages_with_status_12(db_path)
        print(messages_to_send)
        for chat_id in messages_to_send:
            print("djfjksn")
            message = "Ваше сообщение здесь"  # Здесь вы можете формировать сообщение, которое хотите отправить
            await send_message_to_chat(api_token, user_id, chat_id, message, status=1)

if __name__ == "__main__":
    asyncio.run(main())

