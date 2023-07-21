from aiogram import types
from aiogram.dispatcher import Dispatcher

from enkanetwork import EnkaNetworkAPI
from generator import generate_image
import io
from io import BytesIO
from enkaprofile import encprofile

import aiohttp
import asyncio

import sqlite3
from database import create_connection
# Создание объекта EnkaNetworkAPI
enka_api = EnkaNetworkAPI()
bot = None
dp = None

async def send_generated_image(chat_id, image_bytes, caption):
    image_io = io.BytesIO(image_bytes)
    await bot.send_photo(chat_id, photo=image_io, caption=caption)

def chunks(lst, n):
    """Yield successive n-sized chunks from lst."""
    for i in range(0, len(lst), n):
        yield lst[i:i + n]


async def send_characters(message: types.Message):
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
        await message.reply(f"Произошла ошибка при получении данных пользователя: {e}")
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

    result = await encprofile(uid)
    if result and 'img' in result:
        photo = result['img']
        image_output = BytesIO()
        photo.save(image_output, format='PNG')
        image_output.seek(0)
        caption_text = "Выберите персонажа:"
        await bot.send_photo(chat_id=message.chat.id, photo=image_output, caption=caption_text, reply_markup=keyboard)
    else:
        caption_text = "Выберите персонажа:"
        await message.reply(caption_text, reply_markup=keyboard)


async def process_character_callback(callback_query: types.CallbackQuery):
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
            image_buffer = generate_image(user_data, character_info)
            await send_generated_image(
                callback_query.message.chat.id,
                image_buffer.getvalue(),
                character_name,
            )

    await callback_query.answer()
