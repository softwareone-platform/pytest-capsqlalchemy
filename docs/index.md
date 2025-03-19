# pytest-capsqlalchemy

[![Release](https://img.shields.io/github/v/release/softwareone-platform/pytest-capsqlalchemy)](https://img.shields.io/github/v/release/softwareone-platform/pytest-capsqlalchemy)
[![Build status](https://img.shields.io/github/actions/workflow/status/softwareone-platform/pytest-capsqlalchemy/main.yml?branch=main)](https://github.com/softwareone-platform/pytest-capsqlalchemy/actions/workflows/main.yml?query=branch%3Amain)
[![Commit activity](https://img.shields.io/github/commit-activity/m/softwareone-platform/pytest-capsqlalchemy)](https://img.shields.io/github/commit-activity/m/softwareone-platform/pytest-capsqlalchemy)
[![License](https://img.shields.io/github/license/softwareone-platform/pytest-capsqlalchemy)](https://img.shields.io/github/license/softwareone-platform/pytest-capsqlalchemy)

Pytest plugin to allow capturing SQLAlchemy queries.

# Getting Started

## Installation

Install `pytest-capsqlalchemy` via `pip` or your preferred package manager:

```sh
pip install pytest-capsqlalchemy
```

## Configuration

In order to use the fixtures provided by the plugin you also need to define a `db_engine` fixture
in your `conftest.py`. This fixture should return an `AsyncEngine` instance. For example:

```python title="conftest.py"
import pytest
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

@pytest.fixture(scope="session")
def db_engine() -> AsyncEngine:
    return create_async_engine("postgresql+asyncpg://user:pass@localhost:5432/db")
```

## Usage

### Counting number of queries

Here is a basic example with asserts on the number of queries being performed

```python
async def test_query_count(db_session, capsqlalchemy):
    await db_session.execute(text("SELECT 1"))

    capsqlalchemy.assert_query_count(1, include_tcl=False)  # (1)!
    capsqlalchemy.assert_query_count(3, include_tcl=True)   # (2)!
```

1. The `capsqlfixture` starts recording the queries which are sent to the database at the beginning of the test.
   As TCL statements (`BEGIN`, `COMMIT`, `ROLLBACK`) are not included in this assert, only `SELECT 1` is counted
2. This time TCL statements are being counted and since by default SQLAlchemy is configured in `autobegin` mode,
   there are 3 queries which are being counted: `BEGIN`, `SELECT 1` and `ROLLBACK`

### Capturing queries in specific context

You can also use `capqsqlalchemy` as a context manager to check only for the queries being performed in a specific
section of your code. For example:

```python { hl_lines="8-11" }
async def test_context(db_session, capsqlalchemy):
    capsqlalchemy.assert_query_count(0, include_tcl=False)      # (1)!

    await db_session.execute(text("SELECT 1"))
    capsqlalchemy.assert_query_count(1, include_tcl=False)      # (2)!

    with capsqlalchemy:
        await db_session.execute(text("SELECT 2"))
        await db_session.execute(text("SELECT 3"))
        capsqlalchemy.assert_query_count(2, include_tcl=False)  # (3)!

    capsqlalchemy.assert_query_count(3, include_tcl=False)      # (4)!
```

1. No queries have been executed yet
2. Just like in the previous example only `SELECT 1` has been captured yet
3. Since the assert is being performed inside the `with` block only `SELECT 2` and `SELECT 3` will be counted
4. When using a context manager, the outer scope still counts the inner scope queries, so this time all
   `SELECT 1`, `SELECT 2` and `SELECT 3` are captured


### Checking exact queries

You can also write tests that the exact query you expected was generated and exectured by SQLALchemy.
Here's an example with SQLAlchemy 2.0 ORM:

```python
async def test_exact_query(db_session, capsqlalchemy):
    await db_session.execute(select(Order.recipient).where(Order.id == 123))

    capsqlalchemy.assert_captured_queries(  # (1)!
        "SELECT orders.id, orders.recipient \nFROM orders \nWHERE orders.id = :id_1",
        include_tcl=False,
    )

    capsqlalchemy.assert_captured_queries(  # (2)!
        "SELECT orders.id, orders.recipient \nFROM orders \nWHERE orders.id = 123",
        bind_params=True,
        include_tcl=False,
    )
```

1. By default the of the queries will not be binded, so `123` is replaced with `:id_1`
2. If we want to check that the query is **exactly** what we expected we can pass
   `bind_params=True` and we'll get the full query


### Checking the query types

There are also cases where we care about the queries being performed beyond just their count but
we don't care about their structure in such a detail -- that's where we can check that the captured
query _types_ are are what we expect:

```python
from pytest_capsqlalchemy import SQLExpressionType

async def test_query_types(db_session, capsqlalchemy):
    await db_session.execute(select(Order))

    await db_session.commit()

    async with db_session.begin():
        await db_session.execute(select(Order).where(Order.id == 123))
        await db_session.execute(select(text("1")))

        db_session.add(Order(recipient="John Doe"))

    capsqlalchemy.assert_query_types(   # (1)!
        SQLExpressionType.BEGIN,
        SQLExpressionType.SELECT,
        SQLExpressionType.COMMIT,
        SQLExpressionType.BEGIN,
        SQLExpressionType.SELECT,
        SQLExpressionType.SELECT,
        SQLExpressionType.INSERT,
        SQLExpressionType.COMMIT,
    )

    capsqlalchemy.assert_query_types(  # (2)!
        "SELECT",  # (3)!
        "SELECT",
        "SELECT",
        "INSERT",
        include_tcl=False,
    )
```

1. `assert_query_types` allows us to check that the captured queries are a `BEGIN`, a `SELECT`, a `COMMIT` etc. without
   specifying their exact structure
2. Similarly to the other assertion methods, we can exclude the TCL statements if we don't care about them
3. We can also use strings instead of enum values to make the assert shorter to write


!!! warning
    The order of the arguments matters -- it's the same order that the queries have been captured in.

    For example, with the following setup:

    ```python
    await db_session.execute(select(Order))
    db_session.add(Order(recipient="John Doe"))
    ```

    this will pass:

    ```python
    capsqlalchemy.assert_query_types("SELECT", "INSERT", include_tcl=False)
    ```

    but this will fail:

    ```python
    capsqlalchemy.assert_query_types("INSERT", "SELECT", include_tcl=False)
    ```
