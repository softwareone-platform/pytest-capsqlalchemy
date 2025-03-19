import contextlib
import sys
from collections.abc import Mapping
from types import TracebackType
from typing import Any, Optional

if sys.version_info >= (3, 11):  # pragma: no cover
    from typing import Self
else:  # pragma: no cover
    from typing_extensions import Self

from sqlalchemy import Connection, CursorResult, Executable, text
from sqlalchemy.ext.asyncio import AsyncEngine

from pytest_capsqlalchemy.expression import SQLExpression
from pytest_capsqlalchemy.utils import temp_sqlalchemy_event


class SQLAlchemyCaptureContext:
    """Captures expressions executed on a SQLAlchemy engine within a specific context.

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

    See [`SQLAlchemyCapturer`][pytest_capsqlalchemy.capturer.SQLAlchemyCapturer] for the available
    assertions on the captured expressions.
    """

    _engine: AsyncEngine
    _captured_expressions: list[SQLExpression]

    def __init__(self, engine: AsyncEngine):
        """Create a new SQLAlchemyCaptureContext instance."""
        self._engine = engine
        self._captured_expressions = []
        self._sqlaclhemy_events_stack = contextlib.ExitStack()

    @property
    def captured_expressions(self) -> list[SQLExpression]:
        """Returns all SQL expressions captured in the current context."""
        return self._captured_expressions

    def clear(self) -> None:
        """Clear all SQL expressions captured so far in the current context."""
        self._captured_expressions = []

    def _on_begin(self, conn: Connection) -> None:
        self._captured_expressions.append(SQLExpression(executable=text("BEGIN")))

    def _on_commit(self, conn: Connection) -> None:
        self._captured_expressions.append(SQLExpression(executable=text("COMMIT")))

    def _on_rollback(self, conn: Connection) -> None:
        self._captured_expressions.append(SQLExpression(executable=text("ROLLBACK")))

    def _on_after_execute(
        self,
        conn: Connection,
        clauseelement: Executable,
        multiparams: list[dict[str, Any]],
        params: dict[str, Any],
        execution_options: Mapping[str, Any],
        result: CursorResult,
    ) -> None:
        self._captured_expressions.append(
            SQLExpression(executable=clauseelement, params=params, multiparams=multiparams)
        )

    def __enter__(self) -> Self:
        events_stack = self._sqlaclhemy_events_stack.__enter__()

        for event_name, listener in (
            ("begin", self._on_begin),
            ("commit", self._on_commit),
            ("rollback", self._on_rollback),
            ("after_execute", self._on_after_execute),
        ):
            events_stack.enter_context(
                temp_sqlalchemy_event(
                    self._engine.sync_engine,
                    event_name,
                    listener,
                )
            )

        return self

    def __exit__(
        self,
        exc_type: Optional[type[BaseException]],
        exc_value: Optional[BaseException],
        traceback: Optional[TracebackType],
    ) -> Optional[bool]:
        return self._sqlaclhemy_events_stack.__exit__(exc_type, exc_value, traceback)
