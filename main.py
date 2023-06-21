import os
import re
import asyncio
from io import BytesIO
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiohttp import web
from aiogram.types import ChatType
from aiogram.utils.exceptions import Unauthorized
from urllib.parse import quote
from aiogram import Bot, Dispatcher, types
from aiogram.dispatcher.webhook import SendMessage
from aiogram.utils import executor, markdown
from aiogram.types import ParseMode
from config import BOT_TOKEN, WEBHOOK_URL, WEBAPP_HOST, WEBAPP_PORT,WEBHOOK_PATH
from GetInfo import get_player
from enkaprofile import encprofile

TOKEN = BOT_TOKEN
bot = Bot(token=TOKEN)
dp = Dispatcher(bot)
CHAT_ID = 254336259
GROUP_ID = -1001683783876

async def on_startup(dispatcher):
    await dp.bot.set_webhook(WEBHOOK_URL, drop_pending_updates=True)
    
async def on_startup_handler():
    await on_startup(dp)
    
async def on_shutdown(dispatcher):
    await dp.bot.delete_webhook()



def get_region(uid):
    first_digit = int(str(uid)[0])
    if first_digit == 6:
        return "america"
    elif first_digit == 7:
        return "euro"
    elif first_digit == 8:
        return "asia"
    elif first_digit == 9:
        return "sar"
    else:
        return "unknown"
    

# Создание базы данных
import sqlite3
conn = sqlite3.connect("users.db")
cursor = conn.cursor()
cursor.execute("""CREATE TABLE IF NOT EXISTS users
                  (id INTEGER PRIMARY KEY, username TEXT, uid INTEGER, ar INTEGER, nick TEXT, region TEXT, chat_id INTEGER, first_name TEXT)
               """)

async def process_telegram_update(update):
    await dp.process_update(update)
    
async def handle(request):
    if request.match_info.get('token') == BOT_TOKEN:
        data = await request.json()
        update = types.Update(**data)
        await dp.process_update(update)
        return web.Response(text="OK")
    else:
        return web.Response(text="Invalid token")


async def start_command(message: types.Message):
    # user_id = message.from_user.id
    # chat_member = await bot.get_chat_member(chat_id=GROUP_ID, user_id=user_id)
    button_add = types.KeyboardButton('Добавить UID')
    button_donate = types.KeyboardButton('Донат')
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True).add(button_add, button_donate)
    start_text = (
    "Добро пожаловать! Воспользуйтесь кнопками ниже или командами:\n\n"
    "/uid - Показать список всех игроков\n"
    "/uid @nickname - Показать информацию об игроке с данным ником\n"
    "/uid <region> - Показать список игроков для указанного региона (america, euro, asia, sar)\n")
    await message.reply(start_text, reply_markup=keyboard)

async def uid_command(message: types.Message):
    # Check if the message is in a group chat
    if message.chat.type in ["group", "supergroup"]:
        # Получаем информацию о членстве бота в группе
        member = await bot.get_chat_member(chat_id=message.chat.id, user_id=bot.id)
        # Если бот не является администратором или не может удалять сообщения
        if member.status != "administrator" or not member.can_delete_messages:
            # Бот просит пользователя предоставить ему права администратора
            await message.answer("Пожалуйста, дайте мне права администратора для удаления сообщений.")
            return

        # Если бот является администратором и может удалять сообщения, удаляем сообщение пользователя
        await bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)

    args = message.get_args().split()
    show_details = False

    if len(args) == 0:
        cursor.execute("SELECT * FROM users ORDER BY ar DESC, uid ASC")
    elif len(args) == 1:
        query = args[0]
        if query.startswith("@"):
            username = query[1:]
            cursor.execute("SELECT * FROM users WHERE username=?", (username,))
            show_details = True
        elif query in ["asia", "euro", "america", "sar"]: # Or whatever your valid regions are
            region = query
            cursor.execute("SELECT * FROM users WHERE region=? ORDER BY ar DESC, uid ASC", (region,))
        else:
            first_name = query
            cursor.execute("SELECT * FROM users WHERE first_name=?", (first_name,))
            show_details = True
    else:
        await message.answer("Неправильный формат команды. Попробуйте еще раз.")
        return

    result = cursor.fetchall()
    if len(result) == 0:
        await message.answer("Не найдено пользователей.")
        return

    output = ""
    if message.chat.type in ["group", "supergroup"]:
        keyboard = InlineKeyboardMarkup()
        for row in result:
            ar, uid, nickname, username = row[3], row[2], row[4], row[1]
            output += f"AR: {ar} UID: `{uid}` Nick: {nickname}\n"
            if show_details:
                if show_details:
                    output += f"[Подробнее](https://enka.network/u/{uid})\n"
                    result = await encprofile(uid)
                    if 'img' in result:
                        photo = result['img']
                        image_output = BytesIO()
                        photo.save(image_output, format='PNG')
                        image_output.seek(0)
                        await bot.send_photo(chat_id=message.chat.id, photo=image_output)
        keyboard.add(InlineKeyboardButton(f"Добавить свой UID", url=f"https://t.me/akashauz_bot"))
        await message.answer(output, reply_markup=keyboard, parse_mode=types.ParseMode.MARKDOWN_V2)
    else:
        photo = None  # Initialize the variable with a default value
        for row in result:
            ar, uid, nickname, chat_id = row[3], row[2], row[4], row[6]
            output += f"AR: {ar} UID: `{uid}` Nick: [{nickname}](tg://user?id={chat_id})\n"
            if show_details:
                output += f"[Подробнее](https://enka.network/u/{uid})\n"
                result = await encprofile(uid)
                if 'img' in result:
                    photo = result['img']
                    image_output = BytesIO()
                    photo.save(image_output, format='PNG')
                    image_output.seek(0)
                    await bot.send_photo(chat_id=message.chat.id, photo=image_output)
        await message.answer(output, parse_mode=types.ParseMode.MARKDOWN_V2)


#`{uid}`
@dp.message_handler(commands=['update'])
async def update_handler(message: types.Message):
    await update_users_info()
    await update_usernames()
    await message.reply('Обновление пользовательской информации выполнено.')



@dp.message_handler(commands=['db'])
async def update_handler(message: types.Message):
    try:
        with open('users.db', 'rb') as db_file:
            await bot.send_document(CHAT_ID, db_file)
        await message.reply('База данных успешно отправлена!')
    except Exception as e:
        await message.reply(f'Произошла ошибка при отправке базы данных: {str(e)}')

# Обработчик команды /saytlar
@dp.message_handler(commands=['saytlar'])
async def saytlar_command(message: types.Message):
    if message.chat.type not in [ChatType.PRIVATE]:
        # Получаем информацию о членстве бота в группе
        member = await bot.get_chat_member(chat_id=message.chat.id, user_id=bot.id)
        # Если бот не является администратором или не может удалять сообщения
        if member.status != "administrator" or not member.can_delete_messages:
            # Бот просит пользователя предоставить ему права администратора
            await message.answer("Пожалуйста, дайте мне права администратора для удаления сообщений.")
            return

        # Если бот является администратором и может удалять сообщения, удаляем сообщение пользователя
        await bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)
    sites = [
        'genshin.gg',
        'enka.network',
        'game8.co',
        'paimon.moe',
        'hoyolab.com',
        'https://akasha.cv/',
        'genshin.hoyoverse.com/gift',
        'https://genshin.aspirine.su/',
        '@guoba_cardbot',
        '@genshin_gaydlar',
        '@Paimon_Bot'
    ]
    response = '\n'.join(sites)
    await message.answer(response)

# Обработчик команды /bot
@dp.message_handler(commands=['bot'])
async def bot_command(message: types.Message):
    # Проверяем, является ли чат групповым
    if message.chat.type not in [ChatType.PRIVATE]:
        # Получаем информацию о членстве бота в группе
        member = await bot.get_chat_member(chat_id=message.chat.id, user_id=bot.id)
        # Если бот не является администратором или не может удалять сообщения
        if member.status != "administrator" or not member.can_delete_messages:
            # Бот просит пользователя предоставить ему права администратора
            await message.answer("Пожалуйста, дайте мне права администратора для удаления сообщений.")
            return

        # Если бот является администратором и может удалять сообщения, удаляем сообщение пользователя
        await bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)

    # Здесь ответ бота для всех типов чатов
    bots = [
        '@guoba_cardbot',
        '@Genshinaccountlar_bot',
        '@genshin_gaydlar',
        '@Paimon_Bot'
    ]
    response = '\n'.join(bots)
    await message.answer(response)



@dp.message_handler(commands=['start'])
async def start_command_handler(message: types.Message):
    await start_command(message)

@dp.message_handler(commands=["uid"])
async def uid_command_handler(message: types.Message):
    await uid_command(message)


async def add_uid(uid, chat_id, username, first_name):
    player = await get_player(uid)
    if player is None:
        return False
    
    nickname = player.nickname
    ar = player.level
    region = get_region(uid)
    
    # Check if UID already exists in the database
    cursor.execute('SELECT COUNT(*) FROM users WHERE uid = ?', (uid,))
    result = cursor.fetchone()
    if result[0] > 0:
        return False
    
    try:
        cursor.execute('''
            INSERT INTO users (uid, ar, nick, region, chat_id, username, first_name)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (uid, ar, nickname, region, chat_id, username, first_name))
        conn.commit()
    except sqlite3.IntegrityError:
        return False
    return True




@dp.message_handler(lambda message: message.text == 'Донат')
async def donate_handler(message: types.Message):
    await message.answer('https://t.me/genshin_donation/6')
    # здесь можно добавить код для выполнения других действий при нажатии на кнопку "Донат"

@dp.message_handler(lambda message: message.text.startswith("/delete"))
async def delete_handler(message: types.Message):
    if message.chat.id != 254336259:
        await message.answer("У вас нет доступа к этой команде.")
        return

    if len(message.text.split()) < 2:
        await message.answer("Неправильный формат команды. Укажите UID для удаления.")
        return

    uid = int(message.text.split()[1])
    cursor.execute("DELETE FROM users WHERE uid=?", (uid,))
    conn.commit()
    await message.answer("Пользователь с указанным UID удален из списка.")



@dp.message_handler(lambda message: message.text == 'Добавить UID')
async def process_add_uid_command(message: types.Message):
    # Замените этот блок кода на запрос ввода UID, AR и ника от пользователя
    await message.reply("Пожалуйста, введите свой UID:")

@dp.message_handler(lambda message: re.match(r'^[6789]\d{8}$', message.text))
async def process_input_handler(message: types.Message):
    uid = message.text
    chat_id = message.chat.id
    username = message.from_user.username
    first_name = message.from_user.first_name

    uid_pattern = r'^[6789]\d{8}$'
    if not re.match(uid_pattern, uid):
        await message.reply("UID должен состоять из 9 цифр и начинаться с 6, 7, 8 или 9.")
        return

    success = await add_uid(int(uid), chat_id, username, first_name)
    if success:
        await message.reply("UID успешно добавлен!")
    else:
        await message.reply("UID не существует или уже добавлен в базу данных.")


async def update_users_info():
    # Fetch all users from the database
    cursor.execute("SELECT uid FROM users")
    users = cursor.fetchall()

    # Update AR and nickname for each user
    for user in users:
        uid = user[0]
        player = await get_player(uid)

        if player is not None:
            new_ar = player.level
            new_nickname = player.nickname

            # Update user in the database
            cursor.execute("""
                UPDATE users
                SET ar = ?, nick = ?
                WHERE uid = ?
            """, (new_ar, new_nickname, uid))
            conn.commit()


async def update_usernames():
    # Fetch all users from the database
    cursor.execute("SELECT chat_id, username, first_name FROM users")
    users = cursor.fetchall()

    # Update username and first_name for each user
    for user in users:
        chat_id, current_username, current_first_name = user
        user_info = await bot.get_chat(chat_id)

        if user_info is not None:
            new_username = user_info.username
            new_first_name = user_info.first_name

            # Check if username has been added or changed
            if new_username is not None and new_username != current_username:
                cursor.execute("""
                    UPDATE users
                    SET username = ?
                    WHERE chat_id = ?
                """, (new_username, chat_id))
            
            # Check if first_name has been added or changed
            if new_first_name != current_first_name:
                cursor.execute("""
                    UPDATE users
                    SET first_name = ?
                    WHERE chat_id = ?
                """, (new_first_name, chat_id))
            
            conn.commit()



import time
async def backup_db():
    while True:
        await asyncio.sleep(1 * 60 * 60)  # Sleep for 48 hours
        await bot.send_document(CHAT_ID, open('users.db', 'rb'))




# Создание цикла событий
loop = asyncio.get_event_loop_policy().new_event_loop()
asyncio.set_event_loop(loop)
loop.create_task(update_users_info())
loop.create_task(backup_db())

# Для Ноута
# if __name__ == '__main__':
#     from aiogram import executor
#     executor.start_polling(dp, skip_updates=True)




# Для сервера
if __name__ == '__main__':
    executor.start_webhook(dispatcher=dp, webhook_path=WEBHOOK_PATH, on_startup=on_startup, on_shutdown=on_shutdown, host=WEBAPP_HOST, port=WEBAPP_PORT)
