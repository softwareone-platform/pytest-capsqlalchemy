import pytest
from pytest import Pytester


@pytest.fixture(autouse=True)
def setup_asyncio_default_fixture_loop_scope(pytester: Pytester) -> None:
    # This option is set on this project but the tests here are for a brand new one
    # so we need to set it up here too. This is necessary to suppress a warning
    # by pytest-asyncio about the default loop scope.

    pytester.makeini("""
        [pytest]
        asyncio_default_fixture_loop_scope = "session"
    """)


def test_plugin_without_db_engine_fixture(pytester: Pytester) -> None:
    pytester.copy_example("test_missing_setup.py")
    result = pytester.runpytest()

    result.assert_outcomes(errors=1)
    assert "fixture 'db_engine' not found" in result.stdout.str()


def test_plugin_setup_with_async_db_engine_fixture(pytester: Pytester) -> None:
    pytester.copy_example("test_plugin_setup_with_async_db_engine_fixture.py")
    result = pytester.runpytest()

    result.assert_outcomes(passed=3)
