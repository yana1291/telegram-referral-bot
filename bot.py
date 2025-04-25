import os
import sqlite3
from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor
from aiogram.dispatcher.filters import CommandStart

TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_USERNAME = "QE126T"

bot = Bot(token=TOKEN)
dp = Dispatcher(bot)

# Создаем базу данных
conn = sqlite3.connect("referral_bot.db")
cursor = conn.cursor()
cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    invited_by INTEGER,
    balance INTEGER DEFAULT 0
)
""")
cursor.execute("""
CREATE TABLE IF NOT EXISTS purchases (
    user_id INTEGER,
    prize_id INTEGER,
    FOREIGN KEY(user_id) REFERENCES users(user_id)
)
""")
conn.commit()

# Призы
prizes = {
    1: {"name": "0,5 голды", "cost": 50, "message": "Вы приобрели 0,5 голды! Чтобы получить подарок, сделайте скриншот этого сообщения и отправьте его в канал @QE126T."},
    2: {"name": "Приватный доступ в чат", "cost": 30, "message": "Ваша ссылка: https://t.me/joinchat/PrivChatLink"},
    3: {"name": "Промокод на скидку", "cost": 15, "message": "Ваш промокод: PROMO15"}
}

@dp.message_handler(CommandStart(deep_link=True))
async def start_with_ref(message: types.Message):
    ref_id = message.get_args()
    user_id = message.from_user.id

    await message.answer("""Добро пожаловать! Получи свою реферальную ссылку, приглашай друзей и получай Голду!
Для начала проверь подписку на канал: https://t.me/QE126T.""")

    member = await bot.get_chat_member(chat_id=f"@{CHANNEL_USERNAME}", user_id=user_id)
    if member.status in ["member", "administrator", "creator"]:
        cursor.execute("SELECT * FROM users WHERE user_id=?", (user_id,))
        if cursor.fetchone() is None:
            cursor.execute("INSERT INTO users (user_id, invited_by, balance) VALUES (?, ?, ?)", (user_id, ref_id, 0))
            cursor.execute("UPDATE users SET balance = balance + 10 WHERE user_id=?", (ref_id,))
            conn.commit()

        link = f"https://t.me/{(await bot.get_me()).username}?start={user_id}"
        await message.answer(f"Ваша реферальная ссылка:
{link}
Приглашайте друзей и получайте бонусы!")
    else:
        await message.answer("Вы не подписаны на канал. Пожалуйста, подпишитесь на https://t.me/QE126T и нажмите /start заново.")

@dp.message_handler(commands=["start"])
async def start(message: types.Message):
    user_id = message.from_user.id

    await message.answer("""Добро пожаловать! Получи свою реферальную ссылку, приглашай друзей и получай Голду!
Для начала проверь подписку на канал: https://t.me/QE126T.""")

    member = await bot.get_chat_member(chat_id=f"@{CHANNEL_USERNAME}", user_id=user_id)
    if member.status in ["member", "administrator", "creator"]:
        cursor.execute("SELECT * FROM users WHERE user_id=?", (user_id,))
        if cursor.fetchone() is None:
            cursor.execute("INSERT INTO users (user_id, balance) VALUES (?, ?)", (user_id, 0))
            conn.commit()

        link = f"https://t.me/{(await bot.get_me()).username}?start={user_id}"
        await message.answer(f"Ваша реферальная ссылка:
{link}
Приглашайте друзей и получайте бонусы!")
    else:
        await message.answer("Вы не подписаны на канал. Пожалуйста, подпишитесь на https://t.me/QE126T и нажмите /start заново.")

@dp.message_handler(commands=["balance"])
async def balance(message: types.Message):
    user_id = message.from_user.id
    cursor.execute("SELECT balance FROM users WHERE user_id=?", (user_id,))
    result = cursor.fetchone()
    balance = result[0] if result else 0
    await message.answer(f"Ваш текущий баланс: {balance} бонусов")

@dp.message_handler(commands=["shop"])
async def shop(message: types.Message):
    text = "Доступные призы:
"
    for pid, prize in prizes.items():
        text += f"{pid}. {prize['name']} — {prize['cost']} бонусов
"
    text += "
Купить: /buy <номер приза>"
    await message.answer(text)

@dp.message_handler(commands=["buy"])
async def buy(message: types.Message):
    user_id = message.from_user.id
    parts = message.text.split()
    if len(parts) != 2 or not parts[1].isdigit():
        await message.answer("Использование: /buy <номер_приза>")
        return
    prize_id = int(parts[1])
    if prize_id not in prizes:
        await message.answer("Такого приза нет.")
        return
    cursor.execute("SELECT balance FROM users WHERE user_id=?", (user_id,))
    balance = cursor.fetchone()[0]
    if balance < prizes[prize_id]['cost']:
        await message.answer("У вас недостаточно бонусов.")
        return
    cursor.execute("UPDATE users SET balance = balance - ? WHERE user_id=?", (prizes[prize_id]['cost'], user_id))
    cursor.execute("INSERT INTO purchases (user_id, prize_id) VALUES (?, ?)", (user_id, prize_id))
    conn.commit()
    await message.answer(f"Поздравляем! {prizes[prize_id]['message']}")

if __name__ == "__main__":
    executor.start_polling(dp)