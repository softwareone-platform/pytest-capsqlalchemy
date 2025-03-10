from typing import Union

import pytest
from sqlalchemy import Table, delete, insert, select, text, update
from sqlalchemy.sql.ddl import CreateTable

from pytest_capsqlalchemy.expression import SQLExpression, SQLExpressionType
from tests.conftest import Order


@pytest.mark.parametrize(
    ("sql_expression", "expected_type"),
    [
        (SQLExpression(insert(Order)), SQLExpressionType.INSERT),
        (SQLExpression(insert(Order)), "INSERT"),
        (SQLExpression(select(Order)), SQLExpressionType.SELECT),
        (SQLExpression(update(Order)), SQLExpressionType.UPDATE),
        (SQLExpression(delete(Order)), SQLExpressionType.DELETE),
        (SQLExpression(text("BEGIN")), SQLExpressionType.BEGIN),
        (SQLExpression(text("COMMIT")), SQLExpressionType.COMMIT),
        (SQLExpression(text("ROLLBACK")), SQLExpressionType.ROLLBACK),
        (SQLExpression(text("RANDOM TEXT")), SQLExpressionType.UNKNOWN),
        (SQLExpression(CreateTable(Table("some_table", Order.metadata))), SQLExpressionType.UNKNOWN),
    ],
)
def test_sql_expression_type_detection(
    sql_expression: SQLExpression, expected_type: Union[SQLExpressionType, str]
) -> None:
    assert sql_expression.type == expected_type


@pytest.mark.parametrize(
    ("sql_expression_type", "expected_is_tcl"),
    [
        (SQLExpressionType.SELECT, False),
        (SQLExpressionType.INSERT, False),
        (SQLExpressionType.UPDATE, False),
        (SQLExpressionType.DELETE, False),
        (SQLExpressionType.BEGIN, True),
        (SQLExpressionType.COMMIT, True),
        (SQLExpressionType.ROLLBACK, True),
    ],
)
def test_is_tcl_detection(sql_expression_type: SQLExpressionType, expected_is_tcl: bool) -> None:
    assert sql_expression_type.is_tcl == expected_is_tcl


@pytest.mark.parametrize(
    ("sql_expression", "bind_params", "expected_sql"),
    [
        pytest.param(
            SQLExpression(select(Order)),
            False,
            "SELECT orders.id, orders.recipient \nFROM orders",
            id="select_full_table",
        ),
        pytest.param(
            SQLExpression(select(Order.id)),
            False,
            "SELECT orders.id \nFROM orders",
            id="select_single_column",
        ),
        pytest.param(
            SQLExpression(select(Order.id).where(Order.id == 1)),
            False,
            "SELECT orders.id \nFROM orders \nWHERE orders.id = :id_1",
            id="select_where_clause_no_bind_params",
        ),
        pytest.param(
            SQLExpression(select(Order.id).where(Order.id == 1)),
            True,
            "SELECT orders.id \nFROM orders \nWHERE orders.id = 1",
            id="select_where_clause_bind_params",
        ),
        pytest.param(
            SQLExpression(insert(Order)),
            False,
            "INSERT INTO orders (id, recipient) VALUES (:id, :recipient)",
            id="test_raw_insert",
        ),
        pytest.param(
            SQLExpression(insert(Order), params={"recipient": "John Doe"}),
            False,
            "INSERT INTO orders (recipient) VALUES (:recipient)",
            id="insert_single_row_no_bind_params",
        ),
        pytest.param(
            SQLExpression(insert(Order), params={"recipient": "John Doe"}),
            True,
            "INSERT INTO orders (recipient) VALUES ('John Doe')",
            id="insert_single_row_bind_params",
        ),
        pytest.param(
            SQLExpression(insert(Order), multiparams=[{"recipient": "John Doe"}, {"recipient": "Jane Doe"}]),
            False,
            "INSERT INTO orders (recipient) VALUES (:recipient_m0), (:recipient_m1)",
            id="insert_multiple_rows_no_bind_params",
        ),
        pytest.param(
            SQLExpression(insert(Order), multiparams=[{"recipient": "John Doe"}, {"recipient": "Jane Doe"}]),
            True,
            "INSERT INTO orders (recipient) VALUES ('John Doe'), ('Jane Doe')",
            id="insert_multiple_rows_bind_params",
        ),
        pytest.param(
            SQLExpression(update(Order).where(Order.id == 1).values(recipient="John Doe")),
            False,
            "UPDATE orders SET recipient=:recipient WHERE orders.id = :id_1",
            id="update_where_clause_no_bind_params",
        ),
        pytest.param(
            SQLExpression(update(Order).where(Order.id == 1).values(recipient="John Doe")),
            True,
            "UPDATE orders SET recipient='John Doe' WHERE orders.id = 1",
            id="update_where_clause_bind_params",
        ),
        pytest.param(
            SQLExpression(delete(Order).where(Order.id == 1)),
            False,
            "DELETE FROM orders WHERE orders.id = :id_1",
            id="delete_where_clause_no_bind_params",
        ),
        pytest.param(
            SQLExpression(delete(Order).where(Order.id == 1)),
            True,
            "DELETE FROM orders WHERE orders.id = 1",
            id="delete_where_clause_bind_params",
        ),
    ],
)
def test_get_sql(sql_expression: SQLExpression, bind_params: bool, expected_sql: str) -> None:
    assert sql_expression.get_sql(bind_params=bind_params) == expected_sql
