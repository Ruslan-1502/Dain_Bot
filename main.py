import os
import re
import asyncio
import html
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
from characters import characters

TOKEN = BOT_TOKEN
bot = Bot(token=TOKEN)
dp = Dispatcher(bot)
CHAT_ID = 254336259
GROUP_ID = [-1001888345564, -1001883016437, -1001918713467]

async def on_startup(dispatcher):
    await dp.bot.set_webhook(WEBHOOK_URL, drop_pending_updates=True)
    
async def on_startup_handler():
    await on_startup(dp)
    
async def on_shutdown(dispatcher):
    await dp.bot.delete_webhook()



async def check_membership(bot, message: types.Message, GROUP_ID):
    # Если сообщение пришло не из личных сообщений и чат не в списке разрешенных, отвечаем и выходим
    if message.chat.type != 'private' and message.chat.id not in GROUP_ID:
        await message.reply("Я работаю только в группе https://t.me/genshinimpact_uzb")
        return False

    # Проверка, что пользователь является участником хотя бы одной из групп
    for group_id in GROUP_ID:
        try:
            member = await bot.get_chat_member(group_id, message.from_user.id)
            if member.status not in ['left', 'kicked']:
                return True
        except exceptions.BadRequest:
            continue  # Если пользователь не является участником текущей группы, проверяем следующую

    await message.reply("Вы не являетесь участником группы https://t.me/genshinimpact_uzb.")
    return False


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
        try:
            if message.text == '/uid' or message.text == '/uid@akashauz_bot':
                await bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)
        except aiogram.utils.exceptions.MessageToDeleteNotFound:
            await message.answer("Сообщение, которое вы пытаетесь удалить, уже было удалено или не найдено.")

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
            output += f"AR: {ar} UID: <code>{uid}</code> Nick: {nickname}\n"
            if show_details:
                output += f'<a href="https://enka.network/u/{uid}">Подробнее</a>\n'
                result = await encprofile(uid)
                if result and 'img' in result:
                    photo = result['img']
                    image_output = BytesIO()
                    photo.save(image_output, format='PNG')
                    image_output.seek(0)
                    await bot.send_photo(chat_id=message.chat.id, photo=image_output)
        keyboard.add(InlineKeyboardButton(f"Добавить свой UID", url=f"https://t.me/akashauz_bot"))
        await message.answer(output, reply_markup=keyboard, parse_mode=types.ParseMode.HTML)
    else:
        photo = None  # Initialize the variable with a default value
        for row in result:
            ar, uid, nickname, chat_id = row[3], row[2], row[4], row[6]
            output += f"AR: {ar} UID: <code>{uid}</code> Nick: <a href='tg://user?id={chat_id}'>{nickname}</a>\n"
            if show_details:
                output += f'<a href="https://enka.network/u/{uid}">Подробнее</a>\n'
                result = await encprofile(uid)
                if result and 'img' in result:
                    photo = result['img']
                    image_output = BytesIO()
                    photo.save(image_output, format='PNG')
                    image_output.seek(0)
                    await bot.send_photo(chat_id=message.chat.id, photo=image_output)
        await message.answer(output, parse_mode=types.ParseMode.HTML)


#`{uid}`
@dp.message_handler(commands=['update'])
async def update_handler(message: types.Message):
    if message.from_user.id == CHAT_ID:
        await message.reply("Начинаю обновление пользовательской информации...")

        command_args = message.get_args()
        if command_args is None:
            await message.reply("Вы должны указать аргументы команды.")
            return

        # Разбиваем аргументы команды на части
        args = command_args.split('-')
        if len(args) != 2:
            await message.reply("Неверный формат аргументов команды.")
            return

        start_index = int(args[0])
        end_index = int(args[1])

        total_users = await count_users()
        if start_index > end_index or end_index > total_users:
            await message.reply("Неверный диапазон пользователей.")
            return

        users = await get_users(start_index - 1, end_index - start_index + 1)
        await update_users_info(users, message)  # Передаем список пользователей и объект message в функцию

        await message.reply("Обновление завершено.")
    else:
        await message.reply("У вас нет прав для выполнения этой команды.")




CHANNEL_ID = -1001800045281  # замените на ваше число

@dp.message_handler(commands=['gayd'])
async def send_character_guide(message: types.Message):
    words = message.text.split()
    if len(words) >= 2:
        character = words[1].lower().replace(" ", "")
        message_id = characters.get(character)
        if message_id is not None:
            await bot.forward_message(message.chat.id, CHANNEL_ID, message_id, disable_notification=True)
        else:
            await message.answer("У меня нет информации об этом персонаже.")
    else:
        await message.answer("Некорректный формат команды. Пожалуйста, укажите персонажа.")



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
        'ambr.top/ru'
        'genshin.gg',
        'enka.network',
        'game8.co',
        'paimon.moe',
        'hoyolab.com',
        'akasha.cv',
        'genshin.hoyoverse.com/gift',
        'genshin.aspirine.su',
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
    if not await check_membership(bot, message, GROUP_ID):
        return
    await start_command(message)

@dp.message_handler(commands=["uid"])
async def uid_command_handler(message: types.Message):
    if not await check_membership(bot, message, GROUP_ID):
        return
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
    if not await check_membership(bot, message, GROUP_ID):
        return
    # Замените этот блок кода на запрос ввода UID, AR и ника от пользователя
    await message.reply("Пожалуйста, введите свой UID:\n Faqat UID kiriting AR va Nick керакмас:")


@dp.message_handler(lambda message: message.chat.type == 'private')
async def process_input_handler(message: types.Message):
    uid_pattern = r'^[6789]\d{8}$'

    if not re.match(uid_pattern, message.text):
        await message.reply("Неправильный формат UID! UID должен состоять из 9 цифр и начинаться с 6, 7, 8 или 9.")
        return

    uid = message.text
    chat_id = message.chat.id
    username = message.from_user.username
    first_name = message.from_user.first_name

    success = await add_uid(int(uid), chat_id, username, first_name)
    if success:
        await message.reply("UID успешно добавлен!")
    else:
        await message.reply("UID не существует или уже добавлен в базу данных.")


async def update_users_info(users, message):
    total_users = len(users)
    batch_size = 10
    updated_users = 0

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

            updated_users += 1

            if updated_users % batch_size == 0 or updated_users == total_users:
                message_text = f"Обновлено пользователей: {updated_users}/{total_users}"
                await message.reply(message_text)

    message_text = "Обновление пользовательской информации выполнено."
    await message.reply(message_text)


async def count_users():
    cursor.execute("SELECT COUNT(*) FROM users")
    result = cursor.fetchone()
    return result[0]


async def get_users(offset, limit):
    cursor.execute("SELECT uid FROM users LIMIT ?, ?", (offset, limit))
    users = cursor.fetchall()
    return users


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


# Для Ноута
# if name == 'main':
#     from aiogram import executor
#     executor.start_polling(dp, skip_updates=True)


# Для сервера
if __name__ == '__main__':
    executor.start_webhook(dispatcher=dp, webhook_path=WEBHOOK_PATH, on_startup=on_startup, on_shutdown=on_shutdown, host=WEBAPP_HOST, port=WEBAPP_PORT)
