import os
import asyncio
from aiohttp import web
from aiogram import Bot, Dispatcher, types
from aiogram.dispatcher.webhook import SendMessage
from aiogram.utils import executor
from config import BOT_TOKEN, WEBHOOK_URL, WEBAPP_HOST, WEBAPP_PORT,WEBHOOK_PATH,HEROKU_APP_NAME

TOKEN = BOT_TOKEN
bot = Bot(token=TOKEN)
dp = Dispatcher(bot)

def get_region(uid):
    first_digit = int(str(uid)[0])
    if first_digit == 6:
        return "america"
    elif first_digit == 7:
        return "europe"
    elif first_digit == 8:
        return "asia"
    elif first_digit == 9:
        return "sar"
    else:
        return "unknown"
    
async def on_startup(dispatcher):
    await dp.bot.set_webhook(WEBHOOK_URL, drop_pending_updates=True)
    
async def on_startup_handler():
    await on_startup(dp)
    
async def on_shutdown(dispatcher):
    await dp.bot.delete_webhook()

    
# Создание базы данных
import sqlite3
conn = sqlite3.connect("users.db")
cursor = conn.cursor()
cursor.execute("""CREATE TABLE IF NOT EXISTS users
                  (id INTEGER PRIMARY KEY, username TEXT, uid INTEGER, ar INTEGER, nick TEXT, region TEXT)
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

async def add_uid_callback(query: types.CallbackQuery):
    await bot.answer_callback_query(query.id)
    await bot.send_message(chat_id=query.from_user.id, text="Пожалуйста, отправьте свой UID, AR и ник в игре в формате:\nUID AR Nick\nПример: `123456789 45 Player`")

async def donate_callback(query: types.CallbackQuery):
    await bot.answer_callback_query(query.id)
    await bot.send_message(chat_id=query.from_user.id, text="https://t.me/genshin_donation/6")

async def start_command(message: types.Message):
    button_add = types.KeyboardButton('Добавить UID')
    button_donate = types.KeyboardButton('Донат')
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True).add(button_add, button_donate)
    start_text = (
        "Добро пожаловать! Воспользуйтесь кнопками ниже или командами:\n\n"
        "/uid - Показать список всех игроков\n"
        "/uid @nickname - Показать информацию об игроке с данным ником\n"
        "/uid <region> - Показать список игроков для указанного региона (america, europe, asia, sar)\n"
    )
    await message.answer(start_text, reply_markup=keyboard)

async def uid_command(message: types.Message):
    args = message.get_args().split()
    if len(args) == 0:
        cursor.execute("SELECT * FROM users ORDER BY ar DESC")
    elif len(args) == 1 and args[0].startswith("@"):
        username = args[0][1:]
        cursor.execute("SELECT * FROM users WHERE username=?", (username,))
    elif len(args) == 1:
        region = args[0]
        cursor.execute("SELECT * FROM users WHERE region=? ORDER BY ar DESC", (region,))
    else:
        await message.answer("Неправильный формат команды. Попробуйте еще раз.")
        return

    result = cursor.fetchall()
    if len(result) == 0:
        await message.answer("Не найдено пользователей.")
        return

    output = ""
    for row in result:
        ar, uid, nick = row[3], row[2], row[4]
        output += f"AR: {ar} UID: `{uid}` Nick: {nick}\n"

    await message.answer(output, parse_mode=types.ParseMode.MARKDOWN_V2)

@dp.callback_query_handler(lambda c: c.data == "add_uid")
async def add_uid_callback_handler(callback_query: types.CallbackQuery):
    await add_uid_callback(callback_query)

@dp.callback_query_handler(lambda c: c.data == "donate")
async def donate_callback_handler(callback_query: types.CallbackQuery):
    await donate_callback(callback_query)

@dp.message_handler(commands=['start'])
async def start_command_handler(message: types.Message):
    await start_command(message)

@dp.message_handler(commands=["uid"])
async def uid_command_handler(message: types.Message):
    await uid_command(message)

@dp.message_handler(lambda message: message.text.startswith("/delete"))
async def delete_handler(message: types.Message):
    uid = int(message.text.split()[1])
    cursor.execute("DELETE FROM users WHERE uid=?", (uid,))
    conn.commit()
    await message.answer("Пользователь с указанным UID удален из списка.")

@dp.message_handler()
async def process_uid_message(message: types.Message):
    try:
        uid, ar, nick = message.text.split()
        uid, ar = int(uid), int(ar)
        if len(str(uid)) != 9 or not (1 <= ar <= 60):
            raise ValueError("Неправильный формат UID или AR.")
    except ValueError:
        await message.answer("Пожалуйста, отправьте UID, AR и ник в формате:\nUID AR Nick\nПример: `123456789 45 Player`", parse_mode=types.ParseMode.MARKDOWN)
        return

    username = message.from_user.username
    region = get_region(uid)

    cursor.execute("INSERT INTO users (username, uid, ar, nick, region) VALUES (?, ?, ?, ?, ?)", (username, uid, ar, nick, region))
    conn.commit()
    await message.answer("Ваш UID, AR и ник успешно добавлены в список.")

app = web.Application()
app.add_routes([web.post('/{token}', handle)])

if __name__ == '__main__':
    from aiogram import executor
    from aiohttp import web
    executor.start_webhook(dispatcher=dp, webhook_path=WEBHOOK_PATH, on_startup=on_startup, on_shutdown=on_shutdown, host=WEBAPP_HOST, port=WEBAPP_PORT)