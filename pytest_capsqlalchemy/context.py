import contextlib
from collections.abc import Mapping
from types import TracebackType
from typing import Any, Self

from sqlalchemy import Connection, CursorResult, Executable, text
from sqlalchemy.ext.asyncio import AsyncEngine

from pytest_capsqlalchemy.expression import SQLExpression
from pytest_capsqlalchemy.utils import temp_sqlalchemy_event


class SQLAlchemyCaptureContext:
    """
    Captures expressions executed on a SQLAlchemy engine within a specific context.
    These expressions include:

        * SELECT
        * INSERT
        * UPDATE
        * DELETE
        * BEGIN
        * COMMIT
        * ROLLBACK

    Every expression is captured as a SQLExpression object, allowing it to be parsed correctly
    and compared against.

    See SQLAlchemyCapturer for the available assertions on the captured expressions
    """

    engine: AsyncEngine
    captured_expressions: list[SQLExpression]

    def __init__(self, engine: AsyncEngine):
        self.engine = engine
        self.captured_expressions = []
        self.sqlalchemy_events_stack = contextlib.ExitStack()

    def clear(self) -> None:
        self.captured_expressions = []

    def on_begin(self, conn: Connection) -> None:
        self.captured_expressions.append(SQLExpression(executable=text("BEGIN")))

    def on_commit(self, conn: Connection) -> None:
        self.captured_expressions.append(SQLExpression(executable=text("COMMIT")))

    def on_rollback(self, conn: Connection) -> None:
        self.captured_expressions.append(SQLExpression(executable=text("ROLLBACK")))

    def on_after_execute(
        self,
        conn: Connection,
        clauseelement: Executable,
        multiparams: list[dict[str, Any]],
        params: dict[str, Any],
        execution_options: Mapping[str, Any],
        result: CursorResult,
    ) -> None:
        self.captured_expressions.append(
            SQLExpression(executable=clauseelement, params=params, multiparams=multiparams)
        )

    def __enter__(self) -> Self:
        events_stack = self.sqlalchemy_events_stack.__enter__()

        for event_name, listener in (
            ("begin", self.on_begin),
            ("commit", self.on_commit),
            ("rollback", self.on_rollback),
            ("after_execute", self.on_after_execute),
        ):
            events_stack.enter_context(
                temp_sqlalchemy_event(
                    self.engine.sync_engine,
                    event_name,
                    listener,
                )
            )

        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None | bool:
        return self.sqlalchemy_events_stack.__exit__(exc_type, exc_value, traceback)
