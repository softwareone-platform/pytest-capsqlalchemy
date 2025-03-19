from collections.abc import Generator

import pytest
from sqlalchemy.ext.asyncio import AsyncEngine

from pytest_capsqlalchemy import SQLAlchemyCaptureContext, SQLAlchemyCapturer


@pytest.fixture
def capsqlalchemy_context(db_engine: AsyncEngine) -> Generator[SQLAlchemyCaptureContext]:
    """The main fixture to get the [`SQLAlchemyCaptureContext`][pytest_capsqlalchemy.context.SQLAlchemyCaptureContext].

    This is the context for the full test, which captures all SQL expressions executed during the test.

    To capture only the SQL expressions executed within a specific block, use the
    [`capsqlalchemy`][pytest_capsqlalchemy.plugin.capsqlalchemy] fixture.
    """
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

    Returns:
        The capturer object with the full test context already set up.
    """
    return SQLAlchemyCapturer(capsqlalchemy_context)
