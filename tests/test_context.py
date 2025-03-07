from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from pytest_capsqlalchemy.context import SQLAlchemyCaptureContext
from tests.conftest import Order


async def test_capture_session_simple_select(
    capsqlalchemy_context: SQLAlchemyCaptureContext,
    db_session: AsyncSession,
) -> None:
    await db_session.execute(select(text("1")))

    expr_types = [expr.type._value_ for expr in capsqlalchemy_context.captured_expressions]
    assert expr_types == ["BEGIN", "SELECT"]


async def test_capture_session_select_in_explicit_transaction(
    capsqlalchemy_context: SQLAlchemyCaptureContext,
    db_session: AsyncSession,
) -> None:
    async with db_session.begin():
        await db_session.execute(select(text("1")))

    expr_types = [expr.type._value_ for expr in capsqlalchemy_context.captured_expressions]
    assert expr_types == ["BEGIN", "SELECT", "COMMIT"]


async def test_capture_session_mixed_select_statements_multi_transactions(
    capsqlalchemy_context: SQLAlchemyCaptureContext,
    db_session: AsyncSession,
) -> None:
    await db_session.execute(select(text("1")))

    await db_session.rollback()

    async with db_session.begin():
        await db_session.execute(select(text("1")))
        await db_session.execute(select(text("1")))

    await db_session.execute(select(text("1")))
    await db_session.commit()
    await db_session.execute(select(text("1")))

    expr_types = [expr.type._value_ for expr in capsqlalchemy_context.captured_expressions]
    assert expr_types == [
        "BEGIN",
        "SELECT",
        "ROLLBACK",
        "BEGIN",
        "SELECT",
        "SELECT",
        "COMMIT",
        "BEGIN",
        "SELECT",
        "COMMIT",
        "BEGIN",
        "SELECT",
    ]


async def test_clear(
    capsqlalchemy_context: SQLAlchemyCaptureContext,
    db_session: AsyncSession,
) -> None:
    await db_session.execute(select(text("1")))
    await db_session.execute(select(text("1")))

    capsqlalchemy_context.clear()

    await db_session.execute(select(text("1")))

    assert len(capsqlalchemy_context.captured_expressions) == 1
    assert capsqlalchemy_context.captured_expressions[0].type == "SELECT"


async def test_capture_session_add_single_order(
    capsqlalchemy_context: SQLAlchemyCaptureContext,
    db_session: AsyncSession,
) -> None:
    db_session.add(Order(recipient="John Doe"))
    await db_session.commit()

    expr_types = [expr.type._value_ for expr in capsqlalchemy_context.captured_expressions]
    assert expr_types == ["BEGIN", "INSERT", "COMMIT"]

    insert_expr = capsqlalchemy_context.captured_expressions[1]
    assert insert_expr.params == {"recipient": "John Doe"}
    assert insert_expr.multiparams == []


async def test_capture_session_add_multiple_orders(
    capsqlalchemy_context: SQLAlchemyCaptureContext,
    db_session: AsyncSession,
) -> None:
    db_session.add(Order(recipient="John Doe"))
    db_session.add(Order(recipient="Jane Doe"))
    await db_session.commit()

    expr_types = [expr.type._value_ for expr in capsqlalchemy_context.captured_expressions]
    assert expr_types == ["BEGIN", "INSERT", "COMMIT"]

    insert_expr = capsqlalchemy_context.captured_expressions[1]
    assert insert_expr.params == {}
    assert insert_expr.multiparams == [{"recipient": "John Doe"}, {"recipient": "Jane Doe"}]


async def test_capture_session_update_orders(
    capsqlalchemy_context: SQLAlchemyCaptureContext,
    db_session: AsyncSession,
) -> None:
    order = Order(recipient="John Doe")
    db_session.add(order)
    await db_session.commit()

    order.recipient = "Jane Doe"
    await db_session.commit()

    update_expr = next(expr for expr in capsqlalchemy_context.captured_expressions if expr.type == "UPDATE")
    assert update_expr.params == {
        "orders_id": order.id,
        "recipient": "Jane Doe",
    }
    assert update_expr.multiparams == []
