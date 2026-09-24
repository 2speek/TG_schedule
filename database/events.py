from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import Event


async def create_event(
    session: AsyncSession,
    title: str,
    event_type: str,
    start_at: datetime,
    end_at: datetime,
    description: str | None = None,
    location: str | None = None,
    student: str | None = None,
    topic: str | None = None,
    source: str | None = None,
) -> Event:
    event = Event(
        title=title,
        event_type=event_type,
        start_at=start_at,
        end_at=end_at,
        description=description,
        location=location,
        student=student,
        topic=topic,
        source=source,
    )

    session.add(event)

    await session.commit()
    await session.refresh(event)

    return event


async def get_event_by_id(
    session: AsyncSession,
    event_id: int,
) -> Event | None:
    return await session.get(
        Event,
        event_id,
    )


async def get_events(
    session: AsyncSession,
    start_at: datetime | None = None,
    end_at: datetime | None = None,
) -> list[Event]:
    query = (
        select(Event)
        .order_by(Event.start_at)
    )

    if start_at is not None:
        query = query.where(
            Event.start_at >= start_at
        )

    if end_at is not None:
        query = query.where(
            Event.start_at < end_at
        )

    result = await session.execute(query)

    return list(
        result.scalars().all()
    )


async def update_event_title(
    session: AsyncSession,
    event_id: int,
    title: str,
) -> Event | None:
    event = await get_event_by_id(
        session=session,
        event_id=event_id,
    )

    if event is None:
        return None

    event.title = title

    await session.commit()

    return event


async def delete_event(
    session: AsyncSession,
    event: Event,
) -> None:
    await session.delete(event)
    await session.commit()