from collections.abc import Generator

import pytest
from sqlalchemy.ext.asyncio import AsyncEngine

from pytest_capsqlalchemy import SQLAlchemyCaptureContext, SQLAlchemyCapturer


@pytest.fixture
def capsqlalchemy_context(db_engine: AsyncEngine) -> Generator[SQLAlchemyCaptureContext]:
    with SQLAlchemyCaptureContext(db_engine) as capsqlalchemy_ctx:
        yield capsqlalchemy_ctx


@pytest.fixture()
def capsqlalchemy(capsqlalchemy_context: SQLAlchemyCaptureContext) -> SQLAlchemyCapturer:
    """The main fixture to get the [`SQLAlchemyCapturer`][pytest_capsqlalchemy.capturer.SQLAlchemyCapturer].

    Example Usage:

    ```python
    async def test_some_sql_queries(db_session, capsqlalchemy):
        await db_session.execute(select(text("1")))
        capsqlalchemy.assert_query_count(1, include_tcl=False)

        async with capsqlalchemy:
            await db_session.execute(select(text("2")))
            await db_session.execute(select(text("3")))
            capsqlalchemy.assert_query_count(2, include_tcl=False)

        capsqlalchemy.assert_query_count(3, include_tcl=False)
    ```
    """
    return SQLAlchemyCapturer(capsqlalchemy_context)
