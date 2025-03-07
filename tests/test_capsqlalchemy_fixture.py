import pytest
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from pytest_capsqlalchemy import SQLAlchemyCapturer
from tests.conftest import Order, OrderItem


async def test_simple_select(db_session: AsyncSession, capsqlalchemy: SQLAlchemyCapturer) -> None:
    await db_session.execute(text("SELECT 1"))

    capsqlalchemy.assert_query_types("BEGIN", "SELECT")
    capsqlalchemy.assert_query_count(2)


@pytest.mark.parametrize(
    ("include_transaction_queries", "expected_query_count"),
    [
        (True, 9),
        (False, 5),
    ],
)
async def test_assert_query_count(
    db_session: AsyncSession,
    capsqlalchemy: SQLAlchemyCapturer,
    include_transaction_queries: bool,
    expected_query_count: int,
) -> None:
    await db_session.execute(text("SELECT 1"))
    await db_session.execute(select(OrderItem))

    await db_session.commit()

    async with db_session.begin():
        await db_session.execute(select(Order).where(Order.id == 1))
        await db_session.execute(select(text("1")))

        db_session.add(Order(recipient="John Doe"))

    capsqlalchemy.assert_query_count(expected_query_count, include_transaction_queries=include_transaction_queries)


async def test_simple_insert(db_session: AsyncSession, capsqlalchemy: SQLAlchemyCapturer) -> None:
    order = Order(recipient="John Doe")

    db_session.add(order)
    await db_session.commit()

    capsqlalchemy.assert_query_types(
        "BEGIN",
        "INSERT",
        "COMMIT",
    )

    insert_expr = capsqlalchemy.captured_expressions[1]
    assert insert_expr.executable.is_insert
    assert insert_expr.executable.table.name == Order.__tablename__  # type: ignore[attr-defined]
    assert insert_expr.get_sql() == "INSERT INTO orders (recipient) VALUES (:recipient)"
    assert insert_expr.params == {"recipient": "John Doe"}

    assert insert_expr.get_sql(bind_params=True) == "INSERT INTO orders (recipient) VALUES ('John Doe')"

    capsqlalchemy.assert_captured_queries(
        "BEGIN",
        "INSERT INTO orders (recipient) VALUES (:recipient)",
        "COMMIT",
    )

    capsqlalchemy.assert_captured_queries(
        "INSERT INTO orders (recipient) VALUES ('John Doe')",
        include_transaction_queries=False,
        bind_params=True,
    )


async def test_insert_with_relationship(db_session: AsyncSession, capsqlalchemy: SQLAlchemyCapturer) -> None:
    async with db_session.begin():
        order = Order(recipient="John Doe")
        db_session.add(order)
        db_session.add(OrderItem(item_name="Bread", price=2.00, order=order))
        db_session.add(OrderItem(item_name="Butter", price=3.50, order=order))

    capsqlalchemy.assert_captured_queries(
        "INSERT INTO orders (recipient) VALUES (:recipient)",
        (
            "INSERT INTO order_items (item_name, price, order_id) VALUES "
            "(:item_name_m0, :price_m0, :order_id_m0), "
            "(:item_name_m1, :price_m1, :order_id_m1)"
        ),
        include_transaction_queries=False,
    )
