
import os
import sqlite3
from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor
from aiogram.dispatcher.filters import CommandStart
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

TOKEN = os.getenv("BOT_TOKEN")
bot = Bot(token=TOKEN)
dp = Dispatcher(bot)

# База данных
conn = sqlite3.connect("referral_bot.db")
cursor = conn.cursor()
cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    invited_by INTEGER,
    balance INTEGER DEFAULT 0
)
""")
conn.commit()

channel = "@QE126T"

@dp.message_handler(CommandStart(deep_link=True))
@dp.message_handler(commands=["start"])
async def start(message: types.Message):
    keyboard = InlineKeyboardMarkup().add(
        InlineKeyboardButton("Я подписался", callback_data="check_sub")
    )
    await message.answer(
        "Добро пожаловать! Получи свою реферальную ссылку, приглашай друзей и получай Голду!\n"
        "Для начала проверь подписку на канал: https://t.me/QE126T",
        reply_markup=keyboard
    )

@dp.callback_query_handler(lambda c: c.data == "check_sub")
async def check_subscription(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    try:
        member = await bot.get_chat_member(chat_id=channel, user_id=user_id)
        if member.status not in ['member', 'administrator', 'creator']:
            await bot.answer_callback_query(callback_query.id, "Подписка не найдена.")
            return
    except:
        await bot.answer_callback_query(callback_query.id, "Ошибка проверки подписки.")
        return

    # Регистрируем пользователя
    cursor.execute("SELECT * FROM users WHERE user_id=?", (user_id,))
    if cursor.fetchone() is None:
        cursor.execute("INSERT INTO users (user_id, balance) VALUES (?, ?)", (user_id, 0))
        conn.commit()

    link = f"https://t.me/{(await bot.get_me()).username}?start={user_id}"
    await bot.send_message(user_id, f"Ваша реферальная ссылка: {link}")
    await bot.answer_callback_query(callback_query.id)

if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)
