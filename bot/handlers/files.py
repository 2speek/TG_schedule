import random
from pathlib import Path

from aiogram import Bot, F, Router
from aiogram.types import Message
from parsers.file_detector import detect_file_type

router = Router()

UPLOAD_DIR = Path("uploads")


@router.message(F.document)
async def upload_file(
    message: Message,
    bot: Bot,
) -> None:
    UPLOAD_DIR.mkdir(exist_ok=True)
    if message.document.file_name is None:
        file_name = f"{random.randint(1, 10 ** 6)}"
    else:
        file_name = Path(message.document.file_name).name

    file_path = UPLOAD_DIR / file_name
    await bot.download(
        message.document.file_id,
        file_path,
    )
    file_type = detect_file_type(file_path)

    size = message.document.file_size
    if size is None:
        size_text = "неизвестно"
    else:
        size_text = f'{size / 1024:.1f}'
    await message.answer(
        f"Название: {file_name}\nТип: {file_type}\nРазмер: {size_text} KB\nСохранён: {file_path}"
    )
