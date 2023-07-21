from aiogram import types
from aiogram.dispatcher import Dispatcher
import html

from enkanetwork import EnkaNetworkAPI,Assets, EnkaNetworkResponse, Language
from enkanetwork.model.character import CharacterInfo
from generator import generate_image
import io
from io import BytesIO
from enkaprofile import encprofile

import aiohttp
import asyncio
import logging
logging.basicConfig(level=logging.INFO)  # Или DEBUG, если вам нужно больше информации

import sqlite3
from database import create_connection
# Создание объекта EnkaNetworkAPI
enka_api = EnkaNetworkAPI()
bot = None
dp = None

user_button_access = {}

async def send_generated_image(chat_id, image_bytes, caption):
    try:
        logging.info(f"Отправка изображения в чат {chat_id}")
        image_io = io.BytesIO(image_bytes)
        await bot.send_photo(chat_id, photo=image_io, caption=caption)
    except Exception as e:
        logging.error(f"Ошибка при отправке изображения: {e}")
        traceback.print_exc()

def chunks(lst, n):
    """Yield successive n-sized chunks from lst."""
    for i in range(0, len(lst), n):
        yield lst[i:i + n]


async def send_characters(message: types.Message,locale: Language = Language.RU):
    logging.info(f"Обработка сообщения от {message.from_user.id}")
    user_id = message.from_user.id  # Идентификатор пользователя
    user_button_access[user_id] = True  # Позволим пользователю доступ к inline кнопкам
    args = message.get_args()

    if not args:
        await message.reply("Пожалуйста, введите идентификатор пользователя (UID), имя пользователя или имя после команды /card.")
        return

    uid = args

    # Проверка, является ли args числом (т.е. UID)
    if args.isdigit():
        uid = int(args)
    
    # Если args не число, проверим, является ли это именем пользователя или первым именем
    else:
        conn = sqlite3.connect("users.db")
        cursor = conn.cursor()

        # Если args начинается с '@', считаем его именем пользователя
        if args.startswith('@'):
            username = args[1:]  # Удалите '@' из args
            cursor.execute("SELECT uid FROM users WHERE username=?", (username,))
        else:
            # Иначе считаем его первым именем
            cursor.execute("SELECT uid FROM users WHERE first_name=?", (args,))

        result = cursor.fetchone()
        conn.close()

        if result:
            uid = result[0]  # Присвоим uid значение из базы данных

    # Если uid все еще None, мы не смогли найти пользователя
    if uid is None:
        await message.reply("Пользователь не найден. Пожалуйста, введите правильный UID, имя пользователя или имя.")
        return

    try:
        async with enka_api:
            user_data = await enka_api.fetch_user_by_uid(uid)
    except Exception as e:
        await message.reply(f"Такого пользователя нет в Akasha или такого аккаунта с этим UID не существует")
        return

    if not user_data or not user_data.characters:
        await message.reply(f"Пользователь с UID {uid} не найден или у него закрытый стенд.")
        return

    characters = user_data.characters
    keyboard = types.InlineKeyboardMarkup()

    buttons = [
        types.InlineKeyboardButton(text=character.name, callback_data=f'character:{uid}:{character.name}')
        for character in characters
    ]

    for row_buttons in chunks(buttons, 4):
        keyboard.row(*row_buttons)
    caption_text = f"Выберите персонажа:<code>{uid}</code> "
    result = await encprofile(uid)
    if result and 'img' in result:
        photo = result['img']
        image_output = BytesIO()
        photo.save(image_output, format='PNG')
        image_output.seek(0)
        await bot.send_photo(chat_id=message.chat.id, photo=image_output, caption=caption_text, reply_markup=keyboard, 
                             parse_mode=types.ParseMode.HTML)
    else:
        await message.reply(caption_text, reply_markup=keyboard, parse_mode=types.ParseMode.HTML)


import traceback

async def process_character_callback(callback_query: types.CallbackQuery):
    logging.info(f"Обработка callback запроса от {callback_query.from_user.id}")
    user_id = callback_query.from_user.id  # Идентификатор пользователя
    if user_id not in user_button_access or not user_button_access[user_id]:
        await callback_query.answer("Извините, у вас нет доступа к этой функции.")
        return
    try:
        data = callback_query.data.split(':')
        uid = int(data[1])
        character_name = data[2]

        async with enka_api:
            user_data = await enka_api.fetch_user_by_uid(uid)
            characters = user_data.characters
            character_info = next(
                (character for character in characters if character.name == character_name),
                None,
            )

            if character_info:
                image_buffer = await generate_image(user_data, character_info)
                await send_generated_image(
                    callback_query.message.chat.id,
                    image_buffer.getvalue(),
                    character_name,
                )

        await callback_query.answer()
    except Exception as e:
        logging.error(f"Ошибка при обработке callback запроса: {e}")
        traceback.print_exc() 
