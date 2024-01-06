from aiogram import types, Dispatcher, Bot, executor, filters
from aiogram.dispatcher import Dispatcher
import html
import traceback

from enkanetwork import EnkaNetworkAPI,Assets, EnkaNetworkResponse, Language
from enkanetwork.model.character import CharacterInfo
from generator import generate_image
import io
from io import BytesIO
from enkaprofile import encprofile

import aiohttp
import asyncio
import logging
logging.basicConfig(level=logging.INFO)  
import sqlite3
from database import create_connection
# create object EnkaNetworkAPI
enka_api = EnkaNetworkAPI()
bot = None
dp = None


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


last_card_message_id = None  # Переменная для хранения ID последнего сообщения с командой /card

async def send_characters(message: types.Message, bot: Bot, locale: Language = Language.RU):
    global last_card_message_id

    logging.info(f"Обработка сообщения от {message.from_user.id}")
    args = message.get_args()

    # Если args пуст, значит, пользователь отправил только команду /card
    if not args:
        # Получаем chat_id пользователя из базы данных по его user_id
        user_id = message.from_user.id
        conn = create_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT uid FROM users WHERE chat_id=?", (user_id,))
        result = cursor.fetchone()
        conn.close()

        if result:
            uid = result[0]
        else:
            await message.reply("Пожалуйста, введите идентификатор пользователя (UID), имя пользователя или имя после команды /card.")
            return
    else:
        uid = args

        if args.isdigit():
            uid = int(args)
        else:
            conn = create_connection()
            cursor = conn.cursor()

            if args.startswith('@'):
                username = args[1:]
                cursor.execute("SELECT uid FROM users WHERE username=?", (username,))
            else:
                cursor.execute("SELECT uid FROM users WHERE first_name=?", (args,))

            result = cursor.fetchone()
            conn.close()

            if result:
                uid = result[0]

    # Если uid все еще None, мы не смогли найти пользователя
    if uid is None:
        await message.reply("Пользователь не найден. Пожалуйста, введите правильный UID, имя пользователя или имя.")
        return

    try:
        async with enka_api:
            await enka_api.update_assets()
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
        types.InlineKeyboardButton(text=character.name, callback_data=f'character:{uid}:{character.name}:{message.from_user.id}')
        for character in characters
    ]

    for row_buttons in chunks(buttons, 4):
        keyboard.row(*row_buttons)
    caption_text = f"Выберите персонажа:<code>{uid}</code> "
    result = await encprofile(uid)


        # Исправлено: получаем chat_id из объекта message
    chat_id = message.chat.id

    # Удаляем предыдущий ответ на команду /card (если он существует)
    if last_card_message_id:
        try:
            await bot.delete_message(chat_id=chat_id, message_id=last_card_message_id)
        except Exception as e:
            logging.error(f"Ошибка при удалении предыдущего ответа на команду /card: {e}")
            traceback.print_exc()

        # Отправляем новый ответ на команду /card и сохраняем его message_id
        sent_message = await bot.send_photo(chat_id=chat_id, photo=image_output, caption=caption_text, reply_markup=keyboard, 
                             parse_mode=types.ParseMode.HTML)
        last_card_message_id = sent_message.message_id
    else:
        await message.reply(caption_text, reply_markup=keyboard, parse_mode=types.ParseMode.HTML)




async def process_character_callback(callback_query: types.CallbackQuery):
    logging.info(f"Обработка callback запроса от {callback_query.from_user.id}")
    try:
        data = callback_query.data.split(':')
        uid = int(data[1])
        character_name = data[2]
        user_id = int(data[3])
        # Если идентификатор пользователя в callback запросе не совпадает с идентификатором пользователя, который вызвал команду, игнорируем запрос
        if callback_query.from_user.id != user_id:
            await callback_query.answer("У вас нет доступа к этой команде.")
            return
        # Если идентификатор пользователя в callback запросе не совпадает с идентификатором пользователя, который вызвал команду, игнорируем запрос
        if callback_query.from_user.id != user_id:
            await callback_query.answer("У вас нет доступа к этой команде.")
            return
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
