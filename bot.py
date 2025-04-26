import os
import sqlite3
from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils import executor
from aiogram.dispatcher.filters import CommandStart

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

CHANNEL_ID = '@QE126T'  # Сюда вставь свой канал

# Приветствие
@dp.message_handler(CommandStart(deep_link=True))
async def start_with_ref(message: types.Message):
    ref_id = message.get_args()
    user_id = message.from_user.id

    cursor.execute("SELECT * FROM users WHERE user_id=?", (user_id,))
    if cursor.fetchone() is None:
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("✅ Подписался", callback_data=f"checksub:{ref_id}"))
        await message.answer(
            "Добро пожаловать! Получи свою реферальную ссылку, приглашай друзей и получай Голду!\n\n"
            "Для начала проверь подписку на канал: https://t.me/QE126T",
            reply_markup=markup
        )
    else:
        await message.answer("Вы уже зарегистрированы!")

@dp.message_handler(commands=["start"])
async def start(message: types.Message):
    user_id = message.from_user.id

    cursor.execute("SELECT * FROM users WHERE user_id=?", (user_id,))
    if cursor.fetchone() is None:
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("✅ Подписался", callback_data=f"checksub:0"))
        await message.answer(
            "Добро пожаловать! Получи свою реферальную ссылку, приглашай друзей и получай Голду!\n\n"
            "Для начала проверь подписку на канал: https://t.me/QE126T",
            reply_markup=markup
        )
    else:
        await message.answer("Вы уже зарегистрированы!")

# Проверка подписки
@dp.callback_query_handler(lambda c: c.data and c.data.startswith('checksub'))
async def check_subscription(callback_query: types.CallbackQuery):
    ref_id = int(callback_query.data.split(":")[1])
    user_id = callback_query.from_user.id

    member = await bot.get_chat_member(chat_id=CHANNEL_ID, user_id=user_id)
    if member.status in ['member', 'administrator', 'creator']:
        cursor.execute("SELECT * FROM users WHERE user_id=?", (user_id,))
        if cursor.fetchone() is None:
            cursor.execute("INSERT INTO users (user_id, invited_by, balance) VALUES (?, ?, ?)", (user_id, ref_id, 0))
            conn.commit()
            if ref_id != 0:
                cursor.execute("UPDATE users SET balance = balance + 10 WHERE user_id=?", (ref_id,))
                conn.commit()
                await bot.send_message(ref_id, "Поздравляем! Новый пользователь зарегистрировался по вашей ссылке!\n"
                                               "Сделайте скриншот этого сообщения и отправьте его в канал @QE126T для получения 0.5 голды!")

        await bot.send_message(user_id, "Подписка подтверждена! Теперь вы можете приглашать друзей.")
    else:
        await bot.send_message(user_id, "❗ Вы не подписаны на канал!")

if __name__ == "__main__":
    executor.start_polling(dp)