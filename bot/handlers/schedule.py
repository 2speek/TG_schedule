from datetime import date, timedelta

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)

from database.database import async_session
from database.schedule import (
    get_academic_week_info,
    get_schedule_for_date,
)


router = Router()


DAYS = {
    0: "ПОНЕДЕЛЬНИК",
    1: "ВТОРНИК",
    2: "СРЕДА",
    3: "ЧЕТВЕРГ",
    4: "ПЯТНИЦА",
    5: "СУББОТА",
    6: "ВОСКРЕСЕНЬЕ",
}


PERIODICITY_NAMES = {
    "odd": "НЕЧЁТНАЯ",
    "even": "ЧЁТНАЯ",
}


def format_schedule_entry(
    entry,
) -> str:
    """
    Форматирует одно занятие.
    """

    text = (
        f"🕐 {entry.start_time}"
        f"–{entry.end_time}\n"
    )

    if entry.lesson_type:
        text += (
            f"📖 {entry.lesson_type}\n"
        )

    text += (
        f"📚 {entry.subject}"
    )

    if entry.teacher:
        text += (
            f"\n👨‍🏫 {entry.teacher}"
        )

    if entry.location:
        text += (
            f"\n📍 {entry.location}"
        )

    if entry.subgroup:
        text += (
            f"\n👥 {entry.subgroup}"
        )

    return text


def get_main_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="📅 Сегодня",
                    callback_data=(
                        "schedule:today"
                    ),
                ),
                InlineKeyboardButton(
                    text="➡️ Завтра",
                    callback_data=(
                        "schedule:tomorrow"
                    ),
                ),
            ],
            [
                InlineKeyboardButton(
                    text="📚 Эта неделя",
                    callback_data=(
                        "schedule:week"
                    ),
                ),
                InlineKeyboardButton(
                    text="➡️ Следующая неделя",
                    callback_data=(
                        "schedule:nextweek"
                    ),
                ),
            ],
        ]
    )


def get_back_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🏠 Меню",
                    callback_data=(
                        "schedule:menu"
                    ),
                )
            ]
        ]
    )


def get_week_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="⬅️ Предыдущая",
                    callback_data=(
                        "schedule:prevweek"
                    ),
                ),
                InlineKeyboardButton(
                    text="➡️ Следующая",
                    callback_data=(
                        "schedule:nextweek"
                    ),
                ),
            ],
            [
                InlineKeyboardButton(
                    text="🏠 Меню",
                    callback_data=(
                        "schedule:menu"
                    ),
                )
            ],
        ]
    )


def get_monday(
    target_date: date,
) -> date:
    return (
        target_date
        - timedelta(
            days=target_date.weekday()
        )
    )


async def build_day_schedule(
    session,
    target_date: date,
) -> str:
    entries = await get_schedule_for_date(
        session=session,
        target_date=target_date,
    )

    day_name = DAYS[
        target_date.weekday()
    ]

    week_number, periodicity = (
        get_academic_week_info(
            target_date
        )
    )

    periodicity_name = (
        PERIODICITY_NAMES[
            periodicity
        ]
    )

    text = (
        f"📅 {day_name}, "
        f"{target_date:%d.%m.%Y}\n"
        f"📚 Неделя {week_number} — "
        f"{periodicity_name}\n\n"
    )

    if not entries:
        text += "Занятий нет."

        return text

    for entry in entries:
        text += (
            format_schedule_entry(
                entry
            )
        )

        text += "\n\n"

    return text.rstrip()


async def build_week_schedule(
    session,
    monday: date,
    title: str,
) -> str:
    sunday = (
        monday + timedelta(days=6)
    )

    week_number, periodicity = (
        get_academic_week_info(
            monday
        )
    )

    periodicity_name = (
        PERIODICITY_NAMES[
            periodicity
        ]
    )

    text = (
        f"📚 {title}\n"
        f"📅 {monday:%d.%m.%Y} — "
        f"{sunday:%d.%m.%Y}\n"
        f"🔢 Неделя {week_number} — "
        f"{periodicity_name}\n\n"
    )

    for day_offset in range(7):

        target_date = (
            monday
            + timedelta(
                days=day_offset
            )
        )

        day_text = (
            await build_day_schedule(
                session=session,
                target_date=target_date,
            )
        )

        text += day_text
        text += "\n\n"

    return text.rstrip()


async def send_today(
    message: Message,
) -> None:

    today = date.today()

    async with async_session() as session:
        text = (
            await build_day_schedule(
                session=session,
                target_date=today,
            )
        )

    await message.answer(
        text,
        reply_markup=(
            get_back_keyboard()
        ),
    )


async def send_tomorrow(
    message: Message,
) -> None:

    tomorrow = (
        date.today()
        + timedelta(days=1)
    )

    async with async_session() as session:
        text = (
            await build_day_schedule(
                session=session,
                target_date=tomorrow,
            )
        )

    await message.answer(
        text,
        reply_markup=(
            get_back_keyboard()
        ),
    )


async def send_current_week(
    message: Message,
) -> None:

    monday = get_monday(
        date.today()
    )

    async with async_session() as session:
        text = (
            await build_week_schedule(
                session=session,
                monday=monday,
                title=(
                    "РАСПИСАНИЕ "
                    "НА ТЕКУЩУЮ НЕДЕЛЮ"
                ),
            )
        )

    await message.answer(
        text,
        reply_markup=(
            get_week_keyboard()
        ),
    )


async def send_next_week(
    message: Message,
) -> None:

    monday = get_monday(
        date.today()
    )

    next_monday = (
        monday
        + timedelta(days=7)
    )

    async with async_session() as session:
        text = (
            await build_week_schedule(
                session=session,
                monday=next_monday,
                title=(
                    "РАСПИСАНИЕ "
                    "НА СЛЕДУЮЩУЮ НЕДЕЛЮ"
                ),
            )
        )

    await message.answer(
        text,
        reply_markup=(
            get_week_keyboard()
        ),
    )


@router.message(Command("today"))
async def today_schedule(
    message: Message,
) -> None:

    await send_today(
        message
    )


@router.message(Command("tomorrow"))
async def tomorrow_schedule(
    message: Message,
) -> None:

    await send_tomorrow(
        message
    )


@router.message(Command("week"))
async def current_week_schedule(
    message: Message,
) -> None:

    await send_current_week(
        message
    )


@router.message(Command("nextweek"))
async def next_week_schedule(
    message: Message,
) -> None:

    await send_next_week(
        message
    )


# ==========================================================
# CALLBACKS
# ==========================================================


@router.callback_query(
    lambda callback:
    callback.data == "schedule:menu"
)
async def schedule_menu(
    callback: CallbackQuery,
) -> None:

    await callback.message.edit_text(
        "📚 Расписание\n\n"
        "Выбери нужный раздел:",
        reply_markup=(
            get_main_keyboard()
        ),
    )

    await callback.answer()


@router.callback_query(
    lambda callback:
    callback.data == "schedule:today"
)
async def schedule_today_callback(
    callback: CallbackQuery,
) -> None:

    today = date.today()

    async with async_session() as session:
        text = (
            await build_day_schedule(
                session=session,
                target_date=today,
            )
        )

    await callback.message.edit_text(
        text,
        reply_markup=(
            get_back_keyboard()
        ),
    )

    await callback.answer()


@router.callback_query(
    lambda callback:
    callback.data == "schedule:tomorrow"
)
async def schedule_tomorrow_callback(
    callback: CallbackQuery,
) -> None:

    tomorrow = (
        date.today()
        + timedelta(days=1)
    )

    async with async_session() as session:
        text = (
            await build_day_schedule(
                session=session,
                target_date=tomorrow,
            )
        )

    await callback.message.edit_text(
        text,
        reply_markup=(
            get_back_keyboard()
        ),
    )

    await callback.answer()


@router.callback_query(
    lambda callback:
    callback.data == "schedule:week"
)
async def schedule_week_callback(
    callback: CallbackQuery,
) -> None:

    monday = get_monday(
        date.today()
    )

    async with async_session() as session:
        text = (
            await build_week_schedule(
                session=session,
                monday=monday,
                title=(
                    "РАСПИСАНИЕ "
                    "НА ТЕКУЩУЮ НЕДЕЛЮ"
                ),
            )
        )

    await callback.message.edit_text(
        text,
        reply_markup=(
            get_week_keyboard()
        ),
    )

    await callback.answer()


@router.callback_query(
    lambda callback:
    callback.data == "schedule:nextweek"
)
async def schedule_next_week_callback(
    callback: CallbackQuery,
) -> None:

    monday = get_monday(
        date.today()
    )

    next_monday = (
        monday
        + timedelta(days=7)
    )

    async with async_session() as session:
        text = (
            await build_week_schedule(
                session=session,
                monday=next_monday,
                title=(
                    "РАСПИСАНИЕ "
                    "НА СЛЕДУЮЩУЮ НЕДЕЛЮ"
                ),
            )
        )

    await callback.message.edit_text(
        text,
        reply_markup=(
            get_week_keyboard()
        ),
    )

    await callback.answer()


@router.callback_query(
    lambda callback:
    callback.data == "schedule:prevweek"
)
async def schedule_prev_week_callback(
    callback: CallbackQuery,
) -> None:

    monday = get_monday(
        date.today()
    )

    previous_monday = (
        monday
        - timedelta(days=7)
    )

    async with async_session() as session:
        text = (
            await build_week_schedule(
                session=session,
                monday=previous_monday,
                title=(
                    "РАСПИСАНИЕ "
                    "НА ПРЕДЫДУЩУЮ НЕДЕЛЮ"
                ),
            )
        )

    await callback.message.edit_text(
        text,
        reply_markup=(
            get_week_keyboard()
        ),
    )

    await callback.answer()