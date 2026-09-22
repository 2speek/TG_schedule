from datetime import datetime, timedelta

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from database.database import async_session
from database.events import get_events


router = Router()


def format_event(event) -> str:
    start = event.start_at.strftime("%H:%M")
    end = event.end_at.strftime("%H:%M")

    text = (
        f"🕐 {start}–{end}\n"
        f"{event.title}"
    )

    if event.student:
        text += f"\n👤 Ученик: {event.student}"

    if event.topic:
        text += f"\n📚 Тема: {event.topic}"

    if event.location:
        text += f"\n📍 {event.location}"

    return text


@router.message(Command("today"))
async def today_schedule(message: Message) -> None:
    now = datetime.now()

    start_of_day = datetime(
        now.year,
        now.month,
        now.day,
    )

    start_of_next_day = start_of_day + timedelta(days=1)

    async with async_session() as session:
        events = await get_events(
            session=session,
            start_at=start_of_day,
            end_at=start_of_next_day,
        )

    if not events:
        await message.answer(
            "📅 Сегодня событий нет."
        )
        return

    lines = [
        f"📅 Расписание на "
        f"{start_of_day:%d.%m.%Y}\n"
    ]

    for event in events:
        lines.append(format_event(event))
        lines.append("")

    await message.answer("\n".join(lines))


@router.message(Command("events"))
async def all_events(message: Message) -> None:
    async with async_session() as session:
        events = await get_events(session=session)

    if not events:
        await message.answer(
            "🗃 В расписании пока нет событий."
        )
        return

    lines = ["🗃 Все события:\n"]

    for event in events:
        date = event.start_at.strftime("%d.%m.%Y")
        start = event.start_at.strftime("%H:%M")
        end = event.end_at.strftime("%H:%M")

        lines.append(
            f"ID: {event.id}\n"
            f"📅 {date}\n"
            f"🕐 {start}–{end}\n"
            f"{event.title}"
        )

        if event.student:
            lines.append(
                f"👤 Ученик: {event.student}"
            )

        if event.topic:
            lines.append(
                f"📚 Тема: {event.topic}"
            )

        lines.append("")

    await message.answer("\n".join(lines))