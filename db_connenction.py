from contextlib import asynccontextmanager
from typing import Any
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy import select, insert
import models as md
from litestar import Litestar
from litestar.datastructures import State
from passlib.hash import pbkdf2_sha256 as securepwd


# // DATABASE CONFIGURATION
server_name = "postgres"
server_password = "1"
host_address = "localhost"
port = "5432"
database_name = "academicworld"


# // DATABASE SETUP
@asynccontextmanager
async def db_connection(app: Litestar) -> Any:
    engine = create_async_engine(
        f"postgresql+asyncpg://{server_name}:{server_password}@{host_address}:{port}/{database_name}?prepared_statement_cache_size=2048",
        echo=True,
    )
    app.state.engine = engine
    async with engine.begin() as conn:
        # await conn.run_sync(md.Base.metadata.drop_all)
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


# // DATABASE SESSIONMAKER
async def provide_transaction(state: State) -> Any:
    async with async_sessionmaker(state.engine, expire_on_commit=False)() as session:
        async with session.begin():
            yield session
