
import logging
from aiogram import Bot, Dispatcher, executor, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import asyncio

API_TOKEN = 'ВАШ_ТОКЕН_ЗДЕСЬ'
CHANNEL_ID = '@QE126T'

logging.basicConfig(level=logging.INFO)

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

user_data = {}

# Кнопка "Подписался"
subscribe_keyboard = InlineKeyboardMarkup(row_width=1)
subscribe_keyboard.add(InlineKeyboardButton(text="Подписался", callback_data="check_subscription"))

@dp.message_handler(commands=['start'])
async def send_welcome(message: types.Message):
    user_id = message.from_user.id
    referrer_id = None

    if len(message.get_args()) > 0:
        referrer_id = message.get_args()

    user_data[user_id] = {
        'referrer_id': referrer_id,
        'balance': 0
    }

    await message.answer(
        "Добро пожаловать! Получи свою реферальную ссылку, приглашай друзей и получай Голду!
"
        "Для начала проверь подписку на канал: https://t.me/QE126T",
        reply_markup=subscribe_keyboard
    )

@dp.callback_query_handler(lambda c: c.data == 'check_subscription')
async def check_subscription(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    member = await bot.get_chat_member(chat_id=CHANNEL_ID, user_id=user_id)

    if member.status in ['member', 'creator', 'administrator']:
        ref_link = f"https://t.me/{(await bot.me()).username}?start={user_id}"
        await bot.send_message(user_id, f"Вы успешно подписались! Вот ваша реферальная ссылка: {ref_link}")

        referrer_id = user_data.get(user_id, {}).get('referrer_id')
        if referrer_id and int(referrer_id) != user_id:
            user_data[int(referrer_id)]['balance'] += 0.5
            await bot.send_message(
                int(referrer_id),
                "Поздравляем! По вашей ссылке перешёл новый пользователь!
"
                "Отправьте скриншот этого сообщения в канал https://t.me/QE126T для получения 0.5 Голды."
            )
    else:
        await bot.send_message(user_id, "Вы не подписаны на канал!")

@dp.message_handler(commands=['balance'])
async def balance(message: types.Message):
    user_id = message.from_user.id
    balance = user_data.get(user_id, {}).get('balance', 0)
    await message.answer(f"Ваш баланс: {balance} Голды.")

@dp.message_handler(commands=['shop'])
async def shop(message: types.Message):
    await message.answer("Магазин призов:
1. Приз 1 - 1 Голда
2. Приз 2 - 2 Голды")

@dp.message_handler(commands=['buy'])
async def buy(message: types.Message):
    user_id = message.from_user.id
    balance = user_data.get(user_id, {}).get('balance', 0)

    if balance >= 1:
        user_data[user_id]['balance'] -= 1
        await message.answer("Поздравляем с покупкой!")
    else:
        await message.answer("Недостаточно Голды для покупки.")

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
