import asyncio
import logging
from aiogram import Bot, Dispatcher, F
from aiogram.types import LabeledPrice, Message, PreCheckoutQuery
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder

# Настройка логирования
logging.basicConfig(level=logging.INFO)

# ⚠️ ВСТАВЬТЕ СВОЙ ТОКЕН (получите у @BotFather)
BOT_TOKEN = "7674246233:AAHXA8QJI8irAXWN8xdNMhb1KrMP_WDPsyo"

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()


def payment_keyboard():
    builder = InlineKeyboardBuilder()
    builder.button(text=f"Оплатить 20 ⭐️", pay=True)
    return builder.as_markup()


@dp.message(Command("start"))
async def start_command(message: Message):
    await message.answer(
        "👋 Привет! Я тестовый бот для оплаты через Telegram Stars.\n\n"
        "Доступные команды:\n"
        "/donate - сделать пожертвование (20⭐️)\n"
        "/paysupport - информация о возврате средств"
    )


@dp.message(Command("donate"))
async def send_invoice_handler(message: Message):
    prices = [LabeledPrice(label="XTR", amount=20)]
    
    await message.answer_invoice(
        title="Поддержка канала",
        description="Поддержать канал на 20 звёзд!",
        prices=prices,
        provider_token="",
        payload="channel_support",
        currency="XTR",
        reply_markup=payment_keyboard(),
    )


@dp.pre_checkout_query()
async def pre_checkout_handler(pre_checkout_query: PreCheckoutQuery):
    await pre_checkout_query.answer(ok=True)


@dp.message(F.successful_payment)
async def success_payment_handler(message: Message):
    payment_info = message.successful_payment
    amount = payment_info.total_amount
    
    print(f"✅ Платёж от {message.from_user.id}: {amount}⭐️")
    
    await message.answer(
        f"🥳 Спасибо за поддержку! 🤗\n"
        f"Вы пожертвовали {amount}⭐️."
    )


@dp.message(Command("paysupport"))
async def pay_support_handler(message: Message):
    await message.answer(
        "📌 **Информация о возврате средств**\n\n"
        "Добровольные пожертвования не подразумевают возврата средств.\n"
        "Если у вас возникли вопросы, свяжитесь с нами: support@example.com"
    )


async def main():
    print("🚀 Бот запущен...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
