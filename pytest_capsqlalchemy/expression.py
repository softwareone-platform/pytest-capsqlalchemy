from dataclasses import dataclass
from typing import Any

from sqlalchemy import Executable, Insert


@dataclass
class SQLExpression:
    executable: Executable
    params: dict[str, Any] | None
    multiparams: list[dict[str, Any]] | None
    is_tcl: bool = False

    def get_sql(self, *, bind_params: bool = False) -> str:
        expr: Executable
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

        return str(expr.compile(compile_kwargs=compile_kwargs))  # type: ignore[attr-defined]

    @property
    def query_summary(self) -> str:
        return self.get_sql().split()[0].upper()
