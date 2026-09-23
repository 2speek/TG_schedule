from pathlib import Path

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from database.models import Base


DATABASE_FILE = Path("schedule.db")

DATABASE_URL = (
    f"sqlite+aiosqlite:///{DATABASE_FILE}"
)


engine = create_async_engine(
    DATABASE_URL,
    echo=False,
)


async_session = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def init_db() -> None:
    if DATABASE_FILE.exists():
        print(
            f"Используем существующую БД: "
            f"{DATABASE_FILE.resolve()}"
        )
    else:
        print(
            f"БД не найдена. Создаём новую: "
            f"{DATABASE_FILE.resolve()}"
        )

    async with engine.begin() as conn:
        await conn.run_sync(
            Base.metadata.create_all
        )