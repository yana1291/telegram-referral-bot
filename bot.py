
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils import executor

API_TOKEN = 'YOUR_BOT_API_TOKEN'
CHANNEL_ID = '@YOUR_CHANNEL_USERNAME'

logging.basicConfig(level=logging.INFO)

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

# Стартовая кнопка
start_kb = ReplyKeyboardMarkup(resize_keyboard=True)
start_kb.add(KeyboardButton("✅ Подписался"))

# Приветственное сообщение
@dp.message_handler(commands=['start'])
async def send_welcome(message: types.Message):
    await message.answer(
        "Добро пожаловать!
"
        "Получи свою реферальную ссылку, приглашай друзей и получай Голду!
"
        "Для начала проверь подписку на канал: https://t.me/QE126T",
        reply_markup=start_kb
    )

# Проверка подписки
@dp.message_handler(lambda message: message.text == "✅ Подписался")
async def check_subscription(message: types.Message):
    member = await bot.get_chat_member(chat_id=CHANNEL_ID, user_id=message.from_user.id)
    if member.status in ['member', 'administrator', 'creator']:
        await message.answer(f"Вы успешно подписались!
Ваша реферальная ссылка: https://t.me/{(await bot.get_me()).username}?start={message.from_user.id}")
    else:
        await message.answer("Вы ещё не подписаны на канал!")

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
