import enum
from dataclasses import dataclass, field
from typing import Any

from sqlalchemy import ClauseElement, Executable, Insert, TextClause, text


class SQLExpressionType(str, enum.Enum):
    SELECT = "SELECT"
    INSERT = "INSERT"
    UPDATE = "UPDATE"
    DELETE = "DELETE"
    BEGIN = "BEGIN"
    COMMIT = "COMMIT"
    ROLLBACK = "ROLLBACK"
    UNKNOWN = "UNKNOWN"

    @property
    def is_tcl(self) -> bool:
        return self in {SQLExpressionType.BEGIN, SQLExpressionType.COMMIT, SQLExpressionType.ROLLBACK}


@dataclass
class SQLExpression:
    executable: Executable
    params: dict[str, Any] = field(default_factory=dict)
    multiparams: list[dict[str, Any]] = field(default_factory=list)

    def get_sql(self, *, bind_params: bool = False) -> str:
        assert isinstance(self.executable, ClauseElement)

        if self.executable.is_insert:
            assert isinstance(self.executable, Insert)

            if self.multiparams:
                expr = self.executable.values(self.multiparams)
            elif self.params:
                expr = self.executable.values(self.params)
            else:
                expr = self.executable
        else:
            expr = self.executable

        compile_kwargs = {}
        if bind_params:
            compile_kwargs["literal_binds"] = True

        return str(expr.compile(compile_kwargs=compile_kwargs))

    @property
    def type(self) -> SQLExpressionType:
        if self.executable.is_insert:
            return SQLExpressionType.INSERT

        if self.executable.is_select:
            return SQLExpressionType.SELECT

        if self.executable.is_update:
            return SQLExpressionType.UPDATE

        if self.executable.is_delete:
            return SQLExpressionType.DELETE

        if isinstance(self.executable, TextClause):
            if self.executable.compare(text("BEGIN")):
                return SQLExpressionType.BEGIN

            if self.executable.compare(text("COMMIT")):
                return SQLExpressionType.COMMIT

            if self.executable.compare(text("ROLLBACK")):
                return SQLExpressionType.ROLLBACK

        return SQLExpressionType.UNKNOWN
