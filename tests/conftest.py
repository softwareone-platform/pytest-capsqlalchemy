import os
from collections.abc import AsyncGenerator

import pytest
from pytest_asyncio import is_async_test
from sqlalchemy import ForeignKey
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

# Import the plugin fixtures manually since the plugin is explicitly disabled
# in pyproject.toml in order to get accurate coverage reports. The fixtures
# are still useful for the tests, so makes sense to import them here.
from pytest_capsqlalchemy.plugin import *  # noqa: F403

pytest_plugins = ["pytester"]


def pytest_collection_modifyitems(items: list[pytest.Item]) -> None:
    pytest_asyncio_tests = (item for item in items if is_async_test(item))
    session_scope_marker = pytest.mark.asyncio(loop_scope="session")

    for async_test in pytest_asyncio_tests:
        async_test.add_marker(session_scope_marker, append=False)


@pytest.fixture(scope="session")
def db_url() -> str:
    db_name = os.environ["TEST_POSTGRES_DB"]
    db_user = os.environ["TEST_POSTGRES_USER"]
    db_password = os.environ["TEST_POSTGRES_PASSWORD"]
    db_host = os.environ["TEST_POSTGRES_HOST"]
    db_port = os.environ["TEST_POSTGRES_PORT"]

    return f"postgresql+asyncpg://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"


@pytest.fixture(scope="session")
def db_engine(db_url: str) -> AsyncEngine:
    return create_async_engine(db_url, future=True)


@pytest.fixture()
async def db_session(db_engine: AsyncEngine) -> AsyncGenerator[AsyncSession, None]:
    Session = async_sessionmaker(db_engine, class_=AsyncSession, expire_on_commit=False)

    async with Session() as s:
        yield s


# Set up models used only for testing
class TestingBaseModel(DeclarativeBase):
    __test__ = False  # Prevent pytest from trying to collect this class


class Order(TestingBaseModel):
    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    recipient: Mapped[str]
    items: Mapped[list["OrderItem"]] = relationship(back_populates="order", cascade="all, delete-orphan")


class OrderItem(TestingBaseModel):
    __tablename__ = "order_items"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    item_name: Mapped[str]
    price: Mapped[float]
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id"))
    order: Mapped[Order] = relationship(back_populates="items")


@pytest.fixture(scope="session", autouse=True)
async def create_testing_tables(db_engine: AsyncEngine) -> None:
    async with db_engine.begin() as conn:
        await conn.run_sync(TestingBaseModel.metadata.create_all)

    yield

    async with db_engine.begin() as conn:
        await conn.run_sync(TestingBaseModel.metadata.drop_all)
