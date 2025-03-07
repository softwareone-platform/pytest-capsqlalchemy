from types import TracebackType
from typing import Self

from sqlalchemy.ext.asyncio import AsyncEngine

from pytest_capsqlalchemy.context import SQLAlchemyCaptureContext
from pytest_capsqlalchemy.expression import SQLExpression


class SQLAlchemyCapturer:
    """
    The main fixture class for the `capsqlalchemy` plugin. Used to perform asserts
    about the expressions SQLAlchemy has executed during the test.

    Can be used either directly using the assert methods (to perform checks for all expressions
    executed in the test), as a context manager (to perform checks only for the expressions
    executed in a specific block), or a combination of both.

    Intended to be used via the [`capsqlalchemy`][pytest_capsqlalchemy.plugin.capsqlalchemy] fixture
    """

    full_test_context: SQLAlchemyCaptureContext
    partial_context: SQLAlchemyCaptureContext | None

    def __init__(self, full_test_context: SQLAlchemyCaptureContext):
        self.full_test_context = full_test_context
        self.partial_context = None

    @property
    def engine(self) -> AsyncEngine:
        return self.full_test_context.engine

    @property
    def captured_expressions(self) -> list[SQLExpression]:
        if self.partial_context is not None:
            return self.partial_context.captured_expressions

        return self.full_test_context.captured_expressions

    def __enter__(self) -> Self:
        self.partial_context = SQLAlchemyCaptureContext(self.engine)
        self.partial_context = self.partial_context.__enter__()
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None = None,
        exc_val: BaseException | None = None,
        exc_tb: TracebackType | None = None,
    ) -> None | bool:
        if self.partial_context is None:
            raise RuntimeError(f"{self.__class__.__name__}: attempting to call __exit__ before __enter__")

        result = self.partial_context.__exit__(exc_type, exc_val, exc_tb)

        self.partial_context = None

        return result

    def assert_query_types(
        self,
        *expected_query_types: str,
        include_transaction_queries: bool = True,
    ) -> None:
        actual_query_types = []

        for query in self.captured_expressions:
            if not include_transaction_queries and query.is_tcl:
                continue

            actual_query_types.append(query.query_summary)

        assert list(expected_query_types) == actual_query_types

    def assert_query_count(
        self,
        expected_query_count: int,
        *,
        include_transaction_queries: bool = True,
    ) -> None:
        actual_query_count = 0

        for query in self.captured_expressions:
            if not include_transaction_queries and query.is_tcl:
                continue

            actual_query_count += 1

        assert expected_query_count == actual_query_count, (
            f"Query count mismatch: expected {expected_query_count}, got {actual_query_count}"
        )

    def assert_captured_queries(
        self,
        *expected_queries: str,
        include_transaction_queries: bool = True,
        bind_params: bool = False,
    ) -> None:
        actual_queries = []

        for query in self.captured_expressions:
            if not include_transaction_queries and query.is_tcl:
                continue

            actual_queries.append(query.get_sql(bind_params=bind_params))

        assert list(expected_queries) == actual_queries
