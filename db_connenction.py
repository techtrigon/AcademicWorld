from contextlib import asynccontextmanager
from collections.abc import AsyncGenerator
from typing import Any
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy import select, insert
import models as md
from litestar import Litestar
from litestar.datastructures import State
from passlib.hash import pbkdf2_sha256 as securepwd


# -------------------------------------------------------------------------->    DB
@asynccontextmanager
async def db_connection(app: Litestar) -> Any:
    engine = create_async_engine(
        "postgresql+asyncpg://postgres:1@localhost:5432/main4?prepared_statement_cache_size=500",
        # echo=True,
    )
    app.state.engine = engine
    async with engine.begin() as conn:
        await conn.run_sync(md.Base.metadata.drop_all)
        await conn.run_sync(md.Base.metadata.create_all)
        res = await conn.scalar(select(md.User).where(md.User.username == "admin"))
        if res is None:
            await conn.execute(
                insert(md.User).values(
                    name="admin",
                    username="admin",
                    email="admin",
                    pwd=securepwd.hash("admin"),
                    admin=True,
                )
            )
    try:
        yield
    finally:
        await engine.dispose()


# async def provide_transaction(state: State) -> AsyncGenerator[AsyncSession, None]:
async def provide_transaction(state: State) -> Any:
    async with async_sessionmaker(state.engine, expire_on_commit=False)() as session:
        async with session.begin():
            yield session
