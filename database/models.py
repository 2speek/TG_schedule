from datetime import date as date_type, datetime

from sqlalchemy import Date, DateTime, SmallInteger, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class Event(Base):
    __tablename__ = "events"

    id: Mapped[int] = mapped_column(
        primary_key=True,
    )

    title: Mapped[str] = mapped_column(
        String(255),
    )

    event_type: Mapped[str] = mapped_column(
        String(50),
    )

    start_at: Mapped[datetime] = mapped_column(
        DateTime,
    )

    end_at: Mapped[datetime] = mapped_column(
        DateTime,
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    location: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    student: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    topic: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    source: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.now,
    )


class ScheduleEntry(Base):
    __tablename__ = "schedule_entries"

    id: Mapped[int] = mapped_column(
        primary_key=True,
    )

    # 0 — понедельник
    # 1 — вторник
    # 2 — среда
    # 3 — четверг
    # 4 — пятница
    # 5 — суббота
    # 6 — воскресенье
    weekday: Mapped[int] = mapped_column(
        SmallInteger,
        index=True,
    )

    start_time: Mapped[str] = mapped_column(
        String(5),
    )

    end_time: Mapped[str] = mapped_column(
        String(5),
    )

    # every — каждую неделю
    # odd   — нечётная
    # even  — чётная
    periodicity: Mapped[str] = mapped_column(
        String(10),
    )

    lesson_type: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
    )

    subject: Mapped[str] = mapped_column(
        String(500),
    )

    teacher: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )

    location: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    subgroup: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )

    # Одноразовая дата.
    date: Mapped[date_type | None] = mapped_column(
        Date,
        nullable=True,
    )

    # Начало диапазона.
    date_from: Mapped[date_type | None] = mapped_column(
        Date,
        nullable=True,
    )

    # Конец диапазона.
    date_to: Mapped[date_type | None] = mapped_column(
        Date,
        nullable=True,
    )

    source: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.now,
    )