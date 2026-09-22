import re
from dataclasses import dataclass
from typing import Dict, List


@dataclass
class ScheduleEvent:
    start_time: str
    end_time: str

    # every — каждую неделю
    # odd   — нечётная неделя
    # even  — чётная неделя
    periodicity: str

    lesson_type: str = ""
    subject: str = ""

    teacher: str | None = None
    location: str | None = None
    subgroup: str | None = None

    # Для разового события:
    # 22.09.2026
    date: str | None = None

    # Для события с диапазоном:
    # 04.09.2026 — 18.12.2026
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


def parse_schedule_days(text: str) -> Dict[str, List[str]]:
    """
    Разбирает весь текст PDF по дням недели.

    Возвращает:

    {
        "ПОНЕДЕЛЬНИК": [...],
        "ВТОРНИК": [...],
        ...
    }
    """

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


def parse_day_events(lines: list[str]) -> list[str]:
    """
    Объединяет строки одного дня в отдельные события.

    PDF может переносить длинное событие на следующую строку:

        12:45 — 14:20 ■ПР Дискретная математика ...
        К-1006

    В результате должно получиться одно событие:

        12:45 — 14:20 ■ПР Дискретная математика ... К-1006

    Также учитывается ситуация, когда несколько событий
    имеют одно и то же время:

        16:15 — 17:50 ■ПР Иностранный язык ... 323
        ■ПР Иностранный язык ... А-212

    В этом случае второе событие получает время первого.
    """

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

        time_match = time_pattern.match(line)
        lesson_match = lesson_pattern.match(line)

        # --------------------------------------------------
        # Новое событие с явно указанным временем
        # --------------------------------------------------
        if time_match:
            if current_event is not None:
                events.append(current_event)

            current_time = time_match.group(0)
            current_event = line
            continue

        # --------------------------------------------------
        # Новое событие без времени.
        #
        # Например:
        #
        # 16:15 — 17:50 ■ПР ... Подгруппа 1
        # ■ПР ... Подгруппа 2
        # --------------------------------------------------
        if lesson_match:
            if current_event is not None:
                events.append(current_event)

            if current_time is not None:
                current_event = f"{current_time} {line}"
            else:
                current_event = line

            continue

        # --------------------------------------------------
        # Продолжение предыдущего события.
        #
        # Например:
        #
        # 12:45 — 14:20 ■ПР Дискретная математика ...
        # К-1006
        # --------------------------------------------------
        if current_event is not None:
            current_event += " " + line

    if current_event is not None:
        events.append(current_event)

    return events


def parse_event(line: str) -> ScheduleEvent:
    """
    Преобразует строку события в ScheduleEvent.

    Пример входа:

        16:15 — 17:50 ■ПР Иностранный язык
        Подгруппа 1 Самуйлик Т.Ю. 323

    Результат:

        ScheduleEvent(
            start_time="16:15",
            end_time="17:50",
            periodicity="every",
            lesson_type="ПР",
            subject="Иностранный язык",
            teacher="Самуйлик Т.Ю.",
            location="323",
            subgroup="Подгруппа 1",
            ...
        )
    """

    line = line.strip()

    # ======================================================
    # 1. ВРЕМЯ + ПЕРИОДИЧНОСТЬ
    # ======================================================

    time_pattern = re.compile(
        r"^"
        r"(\d{2}:\d{2})"
        r"\s*—\s*"
        r"(\d{2}:\d{2})"
        r"\s*"
        r"([■◩◪])"
    )

    time_match = time_pattern.match(line)

    if time_match is None:
        raise ValueError(
            f"Не удалось распознать время и периодичность: {line}"
        )

    start_time = time_match.group(1)
    end_time = time_match.group(2)
    periodicity_symbol = time_match.group(3)

    periodicity = PERIODICITY_MAP[periodicity_symbol]

    # Всё после времени и символа периодичности
    rest = line[time_match.end():].strip()

    # ======================================================
    # 2. ТИП ЗАНЯТИЯ
    # ======================================================

    lesson_type = ""

    lesson_match = re.match(
        r"^(ЛЕК|ПР|ЛАБ)\b",
        rest,
    )

    if lesson_match:
        lesson_type = lesson_match.group(1)

        rest = rest[
            lesson_match.end():
        ].strip()

    # ======================================================
    # 3. ПОДГРУППА
    # ======================================================

    subgroup = None

    subgroup_match = re.search(
        r"\s*(Подгруппа\s+\d+)",
        rest,
    )

    if subgroup_match:
        subgroup = subgroup_match.group(1)

        rest = (
            rest[:subgroup_match.start()]
            + rest[subgroup_match.end():]
        ).strip()

    # ======================================================
    # 4. ПРЕПОДАВАТЕЛЬ
    # ======================================================

    teacher = None

    teacher_match = re.search(
        r"\s*(.+?)(?=\s*|$)",
        rest,
    )

    if teacher_match:
        teacher = teacher_match.group(1).strip()

        rest = (
            rest[:teacher_match.start()]
            + rest[teacher_match.end():]
        ).strip()

    # ======================================================
    # 5. АУДИТОРИЯ
    # ======================================================

    location = None

    location_match = re.search(
        r"\s*(.+)$",
        rest,
    )

    if location_match:
        location = location_match.group(1).strip()

        rest = rest[
            :location_match.start()
        ].strip()

    # ======================================================
    # 6. ДАТА
    # ======================================================

    date = None
    date_from = None
    date_to = None

    # ------------------------------------------------------
    # Диапазон дат:
    #
    # (04.09.2026 — 18.12.2026)
    # ------------------------------------------------------

    date_range_pattern = re.compile(
        r"\("
        r"(\d{2}\.\d{2}\.\d{4})"
        r"\s*—\s*"
        r"(\d{2}\.\d{2}\.\d{4})"
        r"\)"
    )

    date_range_match = date_range_pattern.search(rest)

    if date_range_match:
        date_from = date_range_match.group(1)
        date_to = date_range_match.group(2)

        rest = (
            rest[:date_range_match.start()]
            + rest[date_range_match.end():]
        ).strip()

    else:
        # --------------------------------------------------
        # Одиночная дата:
        #
        # (22.09.2026)
        # --------------------------------------------------

        date_pattern = re.compile(
            r"\((\d{2}\.\d{2}\.\d{4})\)"
        )

        date_match = date_pattern.search(rest)

        if date_match:
            date = date_match.group(1)

            rest = (
                rest[:date_match.start()]
                + rest[date_match.end():]
            ).strip()

    # ======================================================
    # 7. ПРЕДМЕТ
    # ======================================================

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
        date=date,
        date_from=date_from,
        date_to=date_to,
    )