import re
from dataclasses import dataclass
from typing import Dict, List


@dataclass
class ScheduleEvent:
    start_time: str
    end_time: str

    # every — каждую неделю
    # odd   — нечётная
    # even  — чётная
    periodicity: str

    lesson_type: str = ""
    subject: str = ""

    teacher: str | None = None
    location: str | None = None
    subgroup: str | None = None

    # Одноразовая дата.
    date: str | None = None

    # Диапазон дат.
    date_from: str | None = None
    date_to: str | None = None


DAYS_OF_WEEK = {
    "ПОНЕДЕЛЬНИК",
    "ВТОРНИК",
    "СРЕДА",
    "ЧЕТВЕРГ",
    "ПЯТНИЦА",
    "СУББОТА",
    "ВОСКРЕСЕНЬЕ",
}


PERIODICITY_MAP = {
    "■": "every",
    "◩": "odd",
    "◪": "even",
}


def parse_schedule_days(
    text: str,
) -> Dict[str, List[str]]:
    days: Dict[str, List[str]] = {}

    current_day = None

    for line in text.splitlines():
        line = line.strip()

        if not line:
            continue

        if line in DAYS_OF_WEEK:
            current_day = line
            days[current_day] = []
            continue

        if current_day is not None:
            days[current_day].append(line)

    return days


def parse_day_events(
    lines: list[str],
) -> list[str]:
    events: list[str] = []

    current_event: str | None = None
    current_time: str | None = None

    time_pattern = re.compile(
        r"^\d{2}:\d{2}\s*—\s*\d{2}:\d{2}"
    )

    lesson_pattern = re.compile(
        r"^[■◩◪]"
    )

    for line in lines:
        line = line.strip()

        if not line:
            continue

        time_match = time_pattern.match(
            line
        )

        lesson_match = lesson_pattern.match(
            line
        )

        # Новое событие с временем.
        if time_match:
            if current_event is not None:
                events.append(current_event)

            current_time = (
                time_match.group(0)
            )

            current_event = line

            continue

        # Новое событие без времени.
        if lesson_match:
            if current_event is not None:
                events.append(current_event)

            if current_time is not None:
                current_event = (
                    f"{current_time} {line}"
                )
            else:
                current_event = line

            continue

        # Продолжение предыдущего события.
        if current_event is not None:
            current_event += (
                " " + line
            )

    if current_event is not None:
        events.append(
            current_event
        )

    return events


def parse_event(
    line: str,
) -> ScheduleEvent:

    line = line.strip()

    # ==========================================
    # Время + периодичность
    # ==========================================

    time_pattern = re.compile(
        r"^"
        r"(\d{2}:\d{2})"
        r"\s*—\s*"
        r"(\d{2}:\d{2})"
        r"\s*"
        r"([■◩◪])"
    )

    time_match = time_pattern.match(
        line
    )

    if time_match is None:
        raise ValueError(
            "Не удалось распознать время "
            f"и периодичность: {line}"
        )

    start_time = time_match.group(1)
    end_time = time_match.group(2)

    periodicity_symbol = (
        time_match.group(3)
    )

    periodicity = PERIODICITY_MAP[
        periodicity_symbol
    ]

    rest = line[
        time_match.end():
    ].strip()

    # ==========================================
    # Тип занятия
    # ==========================================

    lesson_type = ""

    lesson_match = re.match(
        r"^(ЛЕК|ПР|ЛАБ)\b",
        rest,
    )

    if lesson_match:
        lesson_type = (
            lesson_match.group(1)
        )

        rest = rest[
            lesson_match.end():
        ].strip()

    # ==========================================
    # Подгруппа
    # ==========================================

    subgroup = None

    subgroup_match = re.search(
        r"\s*(Подгруппа\s+\d+)",
        rest,
    )

    if subgroup_match:
        subgroup = (
            subgroup_match.group(1)
        )

        rest = (
            rest[
                :subgroup_match.start()
            ]
            + rest[
                subgroup_match.end():
            ]
        ).strip()

    # ==========================================
    # Преподаватель
    # ==========================================

    teacher = None

    teacher_match = re.search(
        r"\s*(.+?)(?=\s*|$)",
        rest,
    )

    if teacher_match:
        teacher = (
            teacher_match.group(1)
            .strip()
        )

        rest = (
            rest[
                :teacher_match.start()
            ]
            + rest[
                teacher_match.end():
            ]
        ).strip()

    # ==========================================
    # Аудитория
    # ==========================================

    location = None

    location_match = re.search(
        r"\s*(.+)$",
        rest,
    )

    if location_match:
        location = (
            location_match.group(1)
            .strip()
        )

        rest = rest[
            :location_match.start()
        ].strip()

    # ==========================================
    # Даты
    # ==========================================

    event_date = None
    date_from = None
    date_to = None

    # Диапазон дат.
    date_range_pattern = re.compile(
        r"\("
        r"(\d{2}\.\d{2}\.\d{4})"
        r"\s*—\s*"
        r"(\d{2}\.\d{2}\.\d{4})"
        r"\)"
    )

    date_range_match = (
        date_range_pattern.search(rest)
    )

    if date_range_match:
        date_from = (
            date_range_match.group(1)
        )

        date_to = (
            date_range_match.group(2)
        )

        rest = (
            rest[
                :date_range_match.start()
            ]
            + rest[
                date_range_match.end():
            ]
        ).strip()

    else:
        # Одноразовая дата.
        date_pattern = re.compile(
            r"\((\d{2}\.\d{2}\.\d{4})\)"
        )

        date_match = date_pattern.search(
            rest
        )

        if date_match:
            event_date = (
                date_match.group(1)
            )

            rest = (
                rest[
                    :date_match.start()
                ]
                + rest[
                    date_match.end():
                ]
            ).strip()

    # ==========================================
    # Предмет
    # ==========================================

    subject = rest.strip()

    return ScheduleEvent(
        start_time=start_time,
        end_time=end_time,
        periodicity=periodicity,
        lesson_type=lesson_type,
        subject=subject,
        teacher=teacher,
        location=location,
        subgroup=subgroup,
        date=event_date,
        date_from=date_from,
        date_to=date_to,
    )


def parse_full_schedule(
    text: str,
) -> dict[str, list[ScheduleEvent]]:
    """
    Полностью разбирает расписание из PDF.
    """

    days = parse_schedule_days(
        text
    )

    result: dict[
        str,
        list[ScheduleEvent],
    ] = {}

    for day, lines in days.items():

        events = parse_day_events(
            lines
        )

        result[day] = [
            parse_event(event)
            for event in events
        ]

    return result