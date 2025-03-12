from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from pytest_capsqlalchemy import SQLAlchemyCapturer
from pytest_capsqlalchemy.expression import SQLExpressionType
from tests.conftest import Order, OrderItem


async def test_assert_query_count(db_session: AsyncSession, capsqlalchemy: SQLAlchemyCapturer) -> None:
    await db_session.execute(text("SELECT 1"))
    await db_session.execute(select(OrderItem))

    await db_session.commit()

    async with db_session.begin():
        await db_session.execute(select(Order).where(Order.id == 1))
        await db_session.execute(select(text("1")))

        db_session.add(Order(recipient="John Doe"))

    capsqlalchemy.assert_query_count(9, include_tcl=True)
    capsqlalchemy.assert_query_count(5, include_tcl=False)


async def test_assert_max_query_count(db_session: AsyncSession, capsqlalchemy: SQLAlchemyCapturer) -> None:
    await db_session.execute(text("SELECT 1"))
    await db_session.execute(select(OrderItem))

    await db_session.commit()

    async with db_session.begin():
        await db_session.get(Order, 1)
        await db_session.get(Order, 1)
        await db_session.execute(select(text("1")))

        db_session.add(Order(recipient="John Doe"))

    capsqlalchemy.assert_max_query_count(9, include_tcl=True)
    capsqlalchemy.assert_max_query_count(5, include_tcl=False)


async def test_changing_context(db_session: AsyncSession, capsqlalchemy: SQLAlchemyCapturer) -> None:
    await db_session.execute(text("SELECT 1"))

    capsqlalchemy.assert_query_count(1, include_tcl=False)

    await db_session.execute(text("SELECT 1"))

    capsqlalchemy.assert_query_count(2, include_tcl=False)

    with capsqlalchemy:
        capsqlalchemy.assert_query_count(0, include_tcl=False)
        await db_session.execute(text("SELECT 1"))
        capsqlalchemy.assert_query_count(1, include_tcl=False)

    capsqlalchemy.assert_query_count(3, include_tcl=False)


async def test_captured_queries(db_session: AsyncSession, capsqlalchemy: SQLAlchemyCapturer) -> None:
    await db_session.execute(text("SELECT 1"))
    await db_session.execute(select(OrderItem))

    await db_session.commit()

    async with db_session.begin():
        await db_session.execute(select(Order).where(Order.id == 1))
        await db_session.execute(select(text("1")))

        db_session.add(Order(recipient="John Doe"))

    capsqlalchemy.assert_captured_queries(
        "BEGIN",
        "SELECT 1",
        "SELECT order_items.id, order_items.item_name, order_items.price, order_items.order_id \nFROM order_items",
        "COMMIT",
        "BEGIN",
        "SELECT orders.id, orders.recipient \nFROM orders \nWHERE orders.id = :id_1",
        "SELECT 1",
        "INSERT INTO orders (recipient) VALUES (:recipient)",
        "COMMIT",
    )

    capsqlalchemy.assert_captured_queries(
        "SELECT 1",
        "SELECT order_items.id, order_items.item_name, order_items.price, order_items.order_id \nFROM order_items",
        "SELECT orders.id, orders.recipient \nFROM orders \nWHERE orders.id = :id_1",
        "SELECT 1",
        "INSERT INTO orders (recipient) VALUES (:recipient)",
        include_tcl=False,
    )


async def test_captured_queries_bind_params(db_session: AsyncSession, capsqlalchemy: SQLAlchemyCapturer) -> None:
    await db_session.execute(text("SELECT 1"))
    await db_session.execute(select(OrderItem))

    await db_session.commit()

    async with db_session.begin():
        await db_session.execute(select(Order).where(Order.id == 1))
        await db_session.execute(select(text("1")))

        db_session.add(Order(recipient="John Doe"))

    capsqlalchemy.assert_captured_queries(
        "BEGIN",
        "SELECT 1",
        "SELECT order_items.id, order_items.item_name, order_items.price, order_items.order_id \nFROM order_items",
        "COMMIT",
        "BEGIN",
        "SELECT orders.id, orders.recipient \nFROM orders \nWHERE orders.id = 1",
        "SELECT 1",
        "INSERT INTO orders (recipient) VALUES ('John Doe')",
        "COMMIT",
        bind_params=True,
    )


async def test_captured_query_types(db_session: AsyncSession, capsqlalchemy: SQLAlchemyCapturer) -> None:
    await db_session.execute(select(OrderItem))

    await db_session.commit()

    async with db_session.begin():
        await db_session.execute(select(Order).where(Order.id == 1))
        await db_session.execute(select(text("1")))

        db_session.add(Order(recipient="John Doe"))

    capsqlalchemy.assert_query_types(
        "BEGIN",
        "SELECT",
        "COMMIT",
        "BEGIN",
        "SELECT",
        "SELECT",
        "INSERT",
        "COMMIT",
    )

    capsqlalchemy.assert_query_types(
        SQLExpressionType.SELECT,
        SQLExpressionType.SELECT,
        SQLExpressionType.SELECT,
        SQLExpressionType.INSERT,
        include_tcl=False,
    )


async def test_captured_queries_insert_with_relationship(
    db_session: AsyncSession, capsqlalchemy: SQLAlchemyCapturer
) -> None:
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
        include_tcl=False,
    )

    capsqlalchemy.assert_captured_queries(
        "INSERT INTO orders (recipient) VALUES ('John Doe')",
        (
            "INSERT INTO order_items (item_name, price, order_id) VALUES "  # noqa: S608
            f"('Bread', 2.0, {order.id}), "
            f"('Butter', 3.5, {order.id})"
        ),
        include_tcl=False,
        bind_params=True,
    )
