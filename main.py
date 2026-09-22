import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.filters import CommandStart
from aiogram.types import Message

from bot.handlers.events import router as events_router
from bot.handlers.schedule import router as schedule_router
from bot.handlers.files import router as files_router
from config import BOT_TOKEN
from database.database import init_db


dp = Dispatcher()


@dp.message(CommandStart())
async def cmd_start(message: Message) -> None:
    await message.answer(
        "Привет! 👋\n"
        "Я твой бот для управления расписанием."
    )


async def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
    )

    print("Проверяем базу данных...")
    await init_db()

    dp.include_router(events_router)
    dp.include_router(schedule_router)
    dp.include_router(files_router)

    print("Запускаю Telegram-бота...")

    bot = Bot(token=BOT_TOKEN)

    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())