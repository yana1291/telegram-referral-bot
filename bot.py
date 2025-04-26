
import os
import sqlite3
from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor
from aiogram.dispatcher.filters import CommandStart
import aiohttp

TOKEN = os.getenv("BOT_TOKEN")
bot = Bot(token=TOKEN)
dp = Dispatcher(bot)

# Подключение к базе данных
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

CHANNEL_ID = "@QE126T"  # Укажи сюда свой канал

# Проверка подписки на канал
async def is_subscribed(user_id):
    try:
        member = await bot.get_chat_member(CHANNEL_ID, user_id)
        return member.status in ["member", "administrator", "creator"]
    except Exception:
        return False

# Призы
prizes = {
    1: {"name": "0,5 голды", "cost": 50, "message": "Сделай скриншот этого сообщения и отправь в канал @QE126T."},
    2: {"name": "Приватный доступ в чат", "cost": 30, "message": "Ваша ссылка: https://t.me/joinchat/PrivChatLink"},
    3: {"name": "Промокод на скидку", "cost": 15, "message": "Ваш промокод: PROMO15"}
}

# Старт с реферальной ссылкой
@dp.message_handler(CommandStart(deep_link=True))
async def start_with_ref(message: types.Message):
    ref_id = message.get_args()
    user_id = message.from_user.id

    if not await is_subscribed(user_id):
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("Подписался", callback_data="check_sub"))
        await message.answer(
            "Добро пожаловать! Получи свою реферальную ссылку, приглашай друзей и получай Голду!\n\n"
            "Для начала проверь подписку на канал: https://t.me/QE126T",
            reply_markup=markup
        )
        return

    cursor.execute("SELECT * FROM users WHERE user_id=?", (user_id,))
    if cursor.fetchone() is None:
        cursor.execute("INSERT INTO users (user_id, invited_by, balance) VALUES (?, ?, ?)", (user_id, ref_id, 0))
        conn.commit()

        if ref_id.isdigit():
            cursor.execute("UPDATE users SET balance = balance + 10 WHERE user_id=?", (int(ref_id),))
            conn.commit()
            await bot.send_message(int(ref_id), "Поздравляем! Новый пользователь зарегистрировался по вашей ссылке! Сделайте скриншот этого сообщения и отправьте в канал @QE126T для получения 0,5 голды.")

    await message.answer("Добро пожаловать! Вы успешно зарегистрированы.")

# Старт без реферальной ссылки
@dp.message_handler(commands=["start"])
async def start(message: types.Message):
    user_id = message.from_user.id

    if not await is_subscribed(user_id):
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("Подписался", callback_data="check_sub"))
        await message.answer(
            "Добро пожаловать! Получи свою реферальную ссылку, приглашай друзей и получай Голду!\n\n"
            "Для начала проверь подписку на канал: https://t.me/QE126T",
            reply_markup=markup
        )
        return

    cursor.execute("SELECT * FROM users WHERE user_id=?", (user_id,))
    if cursor.fetchone() is None:
        cursor.execute("INSERT INTO users (user_id, balance) VALUES (?, ?)", (user_id, 0))
        conn.commit()

    await message.answer("Добро пожаловать!")

# Проверка подписки через кнопку
@dp.callback_query_handler(lambda c: c.data == "check_sub")
async def check_subscription(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    if await is_subscribed(user_id):
        link = f"https://t.me/{(await bot.get_me()).username}?start={user_id}"
        await bot.send_message(user_id, f"Ваша реферальная ссылка:\n{link}\nПриглашайте друзей и зарабатывайте бонусы!")
    else:
        await bot.send_message(user_id, "Вы ещё не подписались на канал!")

# Команда /ref
@dp.message_handler(commands=["ref"])
async def ref(message: types.Message):
    user_id = message.from_user.id
    link = f"https://t.me/{(await bot.get_me()).username}?start={user_id}"
    cursor.execute("SELECT COUNT(*) FROM users WHERE invited_by=?", (user_id,))
    count = cursor.fetchone()[0]
    await message.answer(f"Ваша реферальная ссылка:\n{link}\nВы пригласили: {count} человек(а)")

# Команда /balance
@dp.message_handler(commands=["balance"])
async def balance(message: types.Message):
    user_id = message.from_user.id
    cursor.execute("SELECT balance FROM users WHERE user_id=?", (user_id,))
    result = cursor.fetchone()
    balance = result[0] if result else 0
    await message.answer(f"Ваш текущий баланс: {balance} бонусов")

# Команда /shop
@dp.message_handler(commands=["shop"])
async def shop(message: types.Message):
    text = "Доступные призы:\n"
    for pid, prize in prizes.items():
        text += f"{pid}. {prize['name']} — {prize['cost']} бонусов\n"
    text += "\nКупить: /buy <номер приза>"
    await message.answer(text)

# Команда /buy
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
    executor.start_polling(dp, skip_updates=True)
