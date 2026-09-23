import logging
import random
from pathlib import Path

from aiogram import Bot, F, Router
from aiogram.types import Message

from database.database import async_session
from database.schedule import replace_schedule
from parsers.file_detector import detect_file_type
from parsers.pdf_parser import extract_pdf_text
from parsers.schedule_parser import parse_full_schedule


router = Router()

UPLOAD_DIR = Path("uploads")


@router.message(F.document)
async def upload_file(
    message: Message,
    bot: Bot,
) -> None:

    UPLOAD_DIR.mkdir(
        exist_ok=True
    )

    if message.document.file_name is None:
        file_name = (
            f"{random.randint(1, 10 ** 6)}"
        )
    else:
        file_name = Path(
            message.document.file_name
        ).name

    file_path = (
        UPLOAD_DIR / file_name
    )

    await bot.download(
        message.document.file_id,
        file_path,
    )

    file_type = detect_file_type(
        file_path
    )

    size = message.document.file_size

    if size is None:
        size_text = "неизвестно"
    else:
        size_text = (
            f"{size / 1024:.1f}"
        )

    # ==========================================
    # Не PDF
    # ==========================================

    if file_type != "pdf":
        await message.answer(
            f"Название: {file_name}\n"
            f"Тип: {file_type}\n"
            f"Размер: {size_text} KB\n"
            f"Сохранён: {file_path}"
        )

        return

    # ==========================================
    # PDF
    # ==========================================

    try:
        text = extract_pdf_text(
            file_path
        )

        schedule = parse_full_schedule(
            text
        )

        total_events = sum(
            len(events)
            for events in schedule.values()
        )

        async with async_session() as session:
            saved_count = (
                await replace_schedule(
                    session=session,
                    schedule=schedule,
                    source=file_name,
                )
            )

    except Exception:
        logging.exception(
            "Ошибка при обработке PDF: %s",
            file_path,
        )

        await message.answer(
            "❌ Не удалось обработать PDF.\n"
            "Проверь, что это файл с расписанием."
        )

        return

    days_count = len(
        schedule
    )

    await message.answer(
        "✅ Расписание успешно загружено!\n\n"
        f"📄 Файл: {file_name}\n"
        f"📅 Дней: {days_count}\n"
        f"📚 Занятий: {total_events}\n"
        f"💾 Записей в БД: {saved_count}"
    )