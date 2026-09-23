from datetime import date, datetime

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import ScheduleEntry
from parsers.schedule_parser import ScheduleEvent


DAY_TO_WEEKDAY = {
    "ПОНЕДЕЛЬНИК": 0,
    "ВТОРНИК": 1,
    "СРЕДА": 2,
    "ЧЕТВЕРГ": 3,
    "ПЯТНИЦА": 4,
    "СУББОТА": 5,
    "ВОСКРЕСЕНЬЕ": 6,
}


def parse_date(
    value: str | None,
) -> date | None:
    if value is None:
        return None

    return datetime.strptime(
        value,
        "%d.%m.%Y",
    ).date()


def get_academic_week_info(
    target_date: date,
) -> tuple[int, str]:
    """
    Определяет номер и тип учебной недели.

    Семестр начинается 01.09.2026.

    01.09–07.09 -> неделя 1 -> odd
    08.09–14.09 -> неделя 2 -> even
    15.09–21.09 -> неделя 3 -> odd
    22.09–28.09 -> неделя 4 -> even
    29.09–05.10 -> неделя 5 -> odd
    """

    semester_start = date(
        2026,
        9,
        1,
    )

    days_from_start = (
        target_date - semester_start
    ).days

    week_number = (
        days_from_start // 7
    ) + 1

    if week_number % 2 == 1:
        periodicity = "odd"
    else:
        periodicity = "even"

    return (
        week_number,
        periodicity,
    )


async def replace_schedule(
    session: AsyncSession,
    schedule: dict[str, list[ScheduleEvent]],
    source: str | None = None,
) -> int:
    """
    Полностью заменяет расписание.

    Сначала удаляет старые записи schedule_entries,
    затем записывает новое расписание.
    """

    await session.execute(
        delete(ScheduleEntry)
    )

    entries: list[ScheduleEntry] = []

    for day_name, events in schedule.items():

        weekday = DAY_TO_WEEKDAY.get(
            day_name
        )

        if weekday is None:
            continue

        for event in events:
            entry = ScheduleEntry(
                weekday=weekday,
                start_time=event.start_time,
                end_time=event.end_time,
                periodicity=event.periodicity,
                lesson_type=(
                    event.lesson_type
                    or None
                ),
                subject=event.subject,
                teacher=event.teacher,
                location=event.location,
                subgroup=event.subgroup,
                date=parse_date(
                    event.date
                ),
                date_from=parse_date(
                    event.date_from
                ),
                date_to=parse_date(
                    event.date_to
                ),
                source=source,
            )

            entries.append(entry)

    session.add_all(entries)

    await session.commit()

    return len(entries)


async def get_schedule_for_date(
    session: AsyncSession,
    target_date: date,
) -> list[ScheduleEntry]:
    """
    Возвращает занятия,
    которые проходят в указанную дату.
    """

    weekday = target_date.weekday()

    query = (
        select(ScheduleEntry)
        .where(
            ScheduleEntry.weekday == weekday
        )
        .order_by(
            ScheduleEntry.start_time
        )
    )

    result = await session.execute(
        query
    )

    entries = list(
        result.scalars().all()
    )

    _, current_periodicity = (
        get_academic_week_info(
            target_date
        )
    )

    filtered: list[ScheduleEntry] = []

    for entry in entries:

        # ------------------------------
        # Одноразовое событие
        # ------------------------------

        if entry.date is not None:
            if entry.date != target_date:
                continue

        # ------------------------------
        # Диапазон дат
        # ------------------------------

        if entry.date_from is not None:
            if target_date < entry.date_from:
                continue

        if entry.date_to is not None:
            if target_date > entry.date_to:
                continue

        # ------------------------------
        # Каждую неделю
        # ------------------------------

        if entry.periodicity == "every":
            filtered.append(entry)
            continue

        # ------------------------------
        # Нечётная / чётная
        # ------------------------------

        if entry.periodicity == current_periodicity:
            filtered.append(entry)

    return filtered


async def get_all_schedule(
    session: AsyncSession,
) -> list[ScheduleEntry]:
    query = (
        select(ScheduleEntry)
        .order_by(
            ScheduleEntry.weekday,
            ScheduleEntry.start_time,
        )
    )

    result = await session.execute(
        query
    )

    return list(
        result.scalars().all()
    )