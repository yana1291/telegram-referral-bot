
import logging
from aiogram import Bot, Dispatcher, executor, types

API_TOKEN = 'YOUR_TELEGRAM_BOT_API_TOKEN'
CHANNEL_ID = '@YOUR_CHANNEL_USERNAME'

logging.basicConfig(level=logging.INFO)

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

user_data = {}

@dp.message_handler(commands=['start'])
async def send_welcome(message: types.Message):
    args = message.get_args()
    referrer_id = int(args) if args.isdigit() else None
    user_id = message.from_user.id

    if user_id not in user_data:
        user_data[user_id] = {'balance': 0, 'referrals': [], 'referrer': referrer_id}

    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    button = types.KeyboardButton("Подписался")
    keyboard.add(button)

    await message.answer(
        "Добро пожаловать! Получи свою реферальную ссылку, приглашай друзей и получай Голду!
"
        "Для начала проверь подписку на канал: https://t.me/QE126T",
        reply_markup=keyboard
    )

@dp.message_handler(lambda message: message.text == "Подписался")
async def check_subscription(message: types.Message):
    user_id = message.from_user.id
    chat_member = await bot.get_chat_member(chat_id=CHANNEL_ID, user_id=user_id)
    if chat_member.status in ["member", "creator", "administrator"]:
        link = f"https://t.me/YOUR_BOT_USERNAME?start={user_id}"
        await bot.send_message(user_id,
            f"Вы успешно подписались!
"
            f"Ваша реферальная ссылка:
{link}
"
            f"Приглашайте друзей и получайте бонусы!"
        )
        referrer_id = user_data.get(user_id, {}).get('referrer')
        if referrer_id and referrer_id in user_data:
            user_data[referrer_id]['balance'] += 0.5
            await bot.send_message(referrer_id,
                "Поздравляем! Новый пользователь зарегистрировался по вашей ссылке!
"
                "Сделайте скриншот этого сообщения и отправьте его в канал @QE126T для получения 0.5 Голды."
            )
    else:
        await message.answer("Вы ещё не подписались на канал!")

@dp.message_handler(commands=['balance'])
async def check_balance(message: types.Message):
    user_id = message.from_user.id
    balance = user_data.get(user_id, {}).get('balance', 0)
    await message.answer(f"Ваш баланс: {balance} Голды.")

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
