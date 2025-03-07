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
    """The main fixture!"""
    return SQLAlchemyCapturer(capsqlalchemy_context)
