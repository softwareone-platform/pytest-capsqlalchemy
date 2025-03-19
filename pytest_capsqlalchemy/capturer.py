import sys
from types import TracebackType
from typing import Optional, Union

if sys.version_info >= (3, 11):  # pragma: no cover
    from typing import Self
else:  # pragma: no cover
    from typing_extensions import Self

from sqlalchemy.ext.asyncio import AsyncEngine

from pytest_capsqlalchemy.context import SQLAlchemyCaptureContext
from pytest_capsqlalchemy.expression import SQLExpression, SQLExpressionType


class SQLAlchemyCapturer:
    """The main fixture class for the `capsqlalchemy` plugin.

    Used to perform asserts about the expressions SQLAlchemy has executed during the test.

    Can be used either directly using the assert methods (to perform checks for all expressions
    executed in the test), as a context manager (to perform checks only for the expressions
    executed in a specific block), or a combination of both.

    Intended to be used via the [`capsqlalchemy`][pytest_capsqlalchemy.plugin.capsqlalchemy] fixture
    """

    _full_test_context: SQLAlchemyCaptureContext
    _partial_context: Optional[SQLAlchemyCaptureContext]

    def __init__(self, full_test_context: SQLAlchemyCaptureContext):
        """Create a new SQLAlchemyCapturer instance."""
        self._full_test_context = full_test_context
        self._partial_context = None

    @property
    def engine(self) -> AsyncEngine:
        """The SQLAlchemy engine instance being captured."""
        return self._full_test_context._engine

    @property
    def captured_expressions(self) -> list[SQLExpression]:
        """Returns all SQL expressions captured in the current context.

        When used outside a context manager block, returns all expressions captured
        during the entire test. When used inside a context manager block, returns
        only the expressions captured within that specific block.

        This property is useful for performing specific assertions on the captured expressions which
        cannot be easily achieved with the provided assert methods.
        """
        if self._partial_context is not None:
            return self._partial_context.captured_expressions

        return self._full_test_context.captured_expressions

    def __enter__(self) -> Self:
        self._partial_context = SQLAlchemyCaptureContext(self.engine)
        self._partial_context = self._partial_context.__enter__()
        return self

    def __exit__(
        self,
        exc_type: Optional[type[BaseException]] = None,
        exc_val: Optional[BaseException] = None,
        exc_tb: Optional[TracebackType] = None,
    ) -> Optional[bool]:
        if self._partial_context is None:  # pragma: no cover
            raise RuntimeError(f"{self.__class__.__name__}: attempting to call __exit__ before __enter__")

        result = self._partial_context.__exit__(exc_type, exc_val, exc_tb)

        self._partial_context = None

        return result

    def assert_query_types(
        self,
        *expected_query_types: Union[SQLExpressionType, str],
        include_tcl: bool = True,
    ) -> None:
        """Asserts that the captured SQL expressions match the expected query types in order.

        This is useful for ensuring that your code is generating correct query types but
        their exact structure is not important (e.g. complex SELECT statements).

        Args:
            *expected_query_types: Variable number of expected query types
            include_tcl: Whether to include transaction control language statements (BEGIN,
                COMMIT, ROLLBACK) in the comparison

        Raises:
            AssertionError: If the actual query types don't match the expected ones.
        """
        actual_query_types_values = []

        for query in self.captured_expressions:
            if not include_tcl and query.type.is_tcl:
                continue

            actual_query_types_values.append(query.type._value_)

        # Converting to strings as the error message diff will be shorter and more readable
        expected_query_types_values = [
            query_type._value_ if isinstance(query_type, SQLExpressionType) else query_type
            for query_type in expected_query_types
        ]

        assert expected_query_types_values == actual_query_types_values

    def assert_query_count(self, expected_query_count: int, *, include_tcl: bool = True) -> None:
        """Asserts that the number of captured SQL expressions matches the expected count.

        This is useful for ensuring that your code is not generating more statements than expected
        (e.g. due to N+1 queries), however the exact queries are not important.

        Args:
            expected_query_count: The expected number of SQL expressions.
            include_tcl: Whether to include transaction control language statements (BEGIN,
                COMMIT, ROLLBACK) in the count.

        Raises:
            AssertionError: If the actual query count doesn't match the expected count.
        """
        actual_query_count = sum(1 for query in self.captured_expressions if include_tcl or not query.type.is_tcl)

        assert expected_query_count == actual_query_count, (
            f"Query count mismatch: expected {expected_query_count}, got {actual_query_count}"
        )

    def assert_max_query_count(self, expected_max_query_count: int, *, include_tcl: bool = True) -> None:
        """Asserts that the number of captured SQL expressions doesn't exceed the expected count.

        This is useful for ensuring that your code is not generating more statements than expected
        (e.g. due to N+1 queries), however the exact number of queries is not important -- for example
        SQLAlchemy's caching mechanism may generate fewer queries than expected.

        Args:
            expected_max_query_count: The expected maximum number of SQL expressions.
            include_tcl: Whether to include transaction control language statements (BEGIN,
                COMMIT, ROLLBACK) in the count.

        Raises:
            AssertionError: If the actual query count exceeds the expected maximum count.
        """
        actual_query_count = sum(1 for query in self.captured_expressions if include_tcl or not query.type.is_tcl)

        assert expected_max_query_count < actual_query_count, (
            f"Query count mismatch: expected maximum {expected_max_query_count}, got {actual_query_count}"
        )

    def assert_captured_queries(
        self,
        *expected_queries: str,
        include_tcl: bool = True,
        bind_params: bool = False,
    ) -> None:
        """Asserts that the captured SQL queries match the expected SQL strings in order.

        This is useful for ensuring that your code is generating the exact SQL statements you expect.

        Args:
            *expected_queries: Variable number of expected SQL query strings.
            include_tcl: Whether to include transaction control language statements (BEGIN,
                COMMIT, ROLLBACK) in the comparison.
            bind_params: Whether to include bound parameters in the SQL strings. When `False`,
                parameters are represented as placeholders instead.

        Raises:
            AssertionError: If the actual SQL queries don't match the expected ones.
        """
        actual_queries = []

        for query in self.captured_expressions:
            if not include_tcl and query.type.is_tcl:
                continue

            actual_queries.append(query.get_sql(bind_params=bind_params))

        assert list(expected_queries) == actual_queries
