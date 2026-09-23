from datetime import datetime

from aiogram import Router
from aiogram.filters import Command
from aiogram.filters.command import CommandObject
from aiogram.fsm.context import FSMContext
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)

from database.database import async_session
from database.events import (
    create_event,
    delete_event,
    get_event_by_id,
    update_event_title,
)


router = Router()


def format_event(
    event,
) -> str:
    start = event.start_at.strftime(
        "%d.%m.%Y %H:%M"
    )

    end = event.end_at.strftime(
        "%H:%M"
    )

    text = (
        f"📅 {start}–{end}\n"
        f"{event.title}"
    )

    if event.student:
        text += (
            f"\n👤 Ученик: "
            f"{event.student}"
        )

    if event.topic:
        text += (
            f"\n📚 Тема: "
            f"{event.topic}"
        )

    if event.location:
        text += (
            f"\n📍 {event.location}"
        )

    return text


@router.message(Command("add"))
async def add_event(
    message: Message,
    command: CommandObject,
) -> None:
    if not command.args:
        await message.answer(
            "Использование команды:\n\n"
            "/add Название | Тип | Начало | Конец\n\n"
            "Пример:\n"
            "/add Урок английского | student_lesson | "
            "2026-09-21 15:00 | 2026-09-21 16:00"
        )
        return

    parts = [
        part.strip()
        for part in command.args.split("|")
    ]

    if len(parts) != 4:
        await message.answer(
            "Ошибка: нужно указать 4 параметра:\n\n"
            "Название | Тип | Начало | Конец\n\n"
            "Например:\n"
            "/add Урок английского | student_lesson | "
            "2026-09-21 15:00 | 2026-09-21 16:00"
        )
        return

    (
        title,
        event_type,
        start_text,
        end_text,
    ) = parts

    try:
        start_at = datetime.strptime(
            start_text,
            "%Y-%m-%d %H:%M",
        )

        end_at = datetime.strptime(
            end_text,
            "%Y-%m-%d %H:%M",
        )
    except ValueError:
        await message.answer(
            "Ошибка в дате или времени.\n"
            "Используй формат:\n"
            "YYYY-MM-DD HH:MM\n\n"
            "Например:\n"
            "2026-09-21 15:00"
        )
        return

    if end_at <= start_at:
        await message.answer(
            "Ошибка: время окончания "
            "должно быть позже времени начала."
        )
        return

    async with async_session() as session:
        event = await create_event(
            session=session,
            title=title,
            event_type=event_type,
            start_at=start_at,
            end_at=end_at,
            source="telegram",
        )

    await message.answer(
        "✅ Событие добавлено!\n\n"
        f"ID: {event.id}\n"
        f"Название: {event.title}\n"
        f"Тип: {event.event_type}\n"
        f"Начало: "
        f"{event.start_at:%Y-%m-%d %H:%M}\n"
        f"Конец: "
        f"{event.end_at:%Y-%m-%d %H:%M}"
    )


# ==========================================================
# DELETE
# ==========================================================


@router.message(Command("delete"))
async def delete_event_command(
    message: Message,
    command: CommandObject,
) -> None:
    if not command.args:
        await message.answer(
            "Укажи ID события.\n\n"
            "Пример:\n"
            "/delete 2"
        )
        return

    try:
        event_id = int(
            command.args.strip()
        )

    except ValueError:
        await message.answer(
            "ID события должен быть числом.\n\n"
            "Пример:\n"
            "/delete 2"
        )
        return

    async with async_session() as session:
        event = await get_event_by_id(
            session=session,
            event_id=event_id,
        )

        if event is None:
            await message.answer(
                f"Событие с ID {event_id} "
                f"не найдено."
            )
            return

        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="✅ Да, удалить",
                        callback_data=(
                            f"delete_confirm:"
                            f"{event.id}"
                        ),
                    ),
                    InlineKeyboardButton(
                        text="❌ Отмена",
                        callback_data=(
                            f"delete_cancel:"
                            f"{event.id}"
                        ),
                    ),
                ]
            ]
        )

        await message.answer(
            "Вы действительно хотите "
            "удалить событие?\n\n"
            f"{format_event(event)}",
            reply_markup=keyboard,
        )


@router.callback_query(
    lambda callback:
    callback.data
    and callback.data.startswith(
        "delete_confirm:"
    )
)
async def delete_event_confirm(
    callback: CallbackQuery,
) -> None:

    event_id = int(
        callback.data.split(":")[1]
    )

    async with async_session() as session:
        event = await get_event_by_id(
            session=session,
            event_id=event_id,
        )

        if event is None:
            await callback.answer(
                "Событие уже удалено.",
                show_alert=True,
            )
            return

        await delete_event(
            session=session,
            event=event,
        )

    await callback.message.edit_text(
        "✅ Событие удалено."
    )

    await callback.answer()


@router.callback_query(
    lambda callback:
    callback.data
    and callback.data.startswith(
        "delete_cancel:"
    )
)
async def delete_event_cancel(
    callback: CallbackQuery,
) -> None:
    await callback.message.edit_text(
        "❌ Удаление отменено."
    )

    await callback.answer()


# ==========================================================
# EDIT
# ==========================================================


@router.message(Command("edit"))
async def edit_event_command(
    message: Message,
    command: CommandObject,
    state: FSMContext,
) -> None:
    if not command.args:
        await message.answer(
            "Укажи в нужном формате.\n\n"
            "Пример:\n"
            "/edit 2 Пара"
        )
        return

    try:
        event_id = int(
            command.args.split()[0]
        )

    except ValueError:
        await message.answer(
            "ID события должен быть числом.\n\n"
            "Пример:\n"
            "/edit 2 Пара"
        )
        return

    try:
        event_title = (
            command.args.split(
                maxsplit=1
            )[1]
        )

    except IndexError:
        await message.answer(
            "Введи название для изменения.\n\n"
            "Пример:\n"
            "/edit 2 Пара"
        )
        return

    async with async_session() as session:
        event = await get_event_by_id(
            session=session,
            event_id=event_id,
        )

        if event is None:
            await message.answer(
                f"Событие с ID {event_id} "
                f"не найдено."
            )
            return

        await state.update_data(
            new_title=event_title
        )

        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="✅ Да, заменить",
                        callback_data=(
                            f"edit_confirm:"
                            f"{event.id}"
                        ),
                    ),
                    InlineKeyboardButton(
                        text="❌ Отмена",
                        callback_data=(
                            f"edit_cancel:"
                            f"{event.id}"
                        ),
                    ),
                ]
            ]
        )

        await message.answer(
            "Вы действительно хотите "
            "изменить событие?\n\n"
            f"{format_event(event)}",
            reply_markup=keyboard,
        )


@router.callback_query(
    lambda callback:
    callback.data
    and callback.data.startswith(
        "edit_confirm:"
    )
)
async def edit_event_confirm(
    callback: CallbackQuery,
    state: FSMContext,
) -> None:

    event_id = int(
        callback.data.split(":")[1]
    )

    data = await state.get_data()

    event_title = data.get(
        "new_title"
    )

    if not event_title:
        await callback.answer(
            "Данные для изменения "
            "не найдены.",
            show_alert=True,
        )
        return

    async with async_session() as session:

        event = await update_event_title(
            session=session,
            event_id=event_id,
            title=event_title,
        )

        if event is None:
            await callback.answer(
                "Событие не найдено.",
                show_alert=True,
            )
            await state.clear()
            return

    await callback.message.edit_text(
        "✅ Событие изменено."
    )
    await state.clear()
    await callback.answer()


@router.callback_query(
    lambda callback:
    callback.data
    and callback.data.startswith(
        "edit_cancel:"
    )
)
async def edit_event_cancel(
    callback: CallbackQuery,
    state: FSMContext,
) -> None:
    await callback.message.edit_text(
        "❌ Изменение отменено."
    )
    await state.clear()
    await callback.answer()