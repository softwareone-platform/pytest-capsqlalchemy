import contextlib
from collections.abc import Callable, Generator
from typing import Any

from sqlalchemy import event


@contextlib.contextmanager
def temp_sqlalchemy_event(
    target: Any,
    identifier: str,
    fn: Callable[..., Any],
    *args: Any,
    **kwargs: Any,
) -> Generator[None, None, None]:
    """Temporarily add a SQLAlchemy event listener to the target object.

    The event listener is automatically removed when the context manager exits.
    """
    event.listen(target, identifier, fn, *args, **kwargs)

    try:
        yield
    finally:
        event.remove(target, identifier, fn)
