from pytest import Pytester


def test_plugin_without_db_engine_fixture(pytester: Pytester) -> None:
    pytester.makepyfile("""
        def test_capsqlalchemy_setup(capsqlalchemy):
            pass
    """)

    result = pytester.runpytest("--asyncio-mode=strict")

    result.assert_outcomes(errors=1)
    assert "fixture 'db_engine' not found" in result.stdout.str()


def test_plugin_setup_with_async_db_engine_fixture(pytester: Pytester) -> None:
    pytester.makeconftest("""
        import pytest
        import os
        from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

        @pytest.fixture(scope="session")
        def db_url() -> str:
            db_name = os.environ["TEST_POSTGRES_DB"]
            db_user = os.environ["TEST_POSTGRES_USER"]
            db_password = os.environ["TEST_POSTGRES_PASSWORD"]
            db_host = os.environ["TEST_POSTGRES_HOST"]
            db_port = os.environ["TEST_POSTGRES_PORT"]

            return f"postgresql+asyncpg://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"

        @pytest.fixture(scope="session")
        def db_engine(db_url: str) -> AsyncEngine:
            return create_async_engine(db_url, future=True)
    """)

    pytester.makepyfile("""
        import pytest
        from sqlalchemy import text

        def test_capsqlalchemy_setup(capsqlalchemy):
            pass

        def test_capsqlalchemy_initial_query_count(capsqlalchemy):
            capsqlalchemy.assert_query_count(0)

        @pytest.mark.asyncio
        async def test_capsqlalchemy_counts_executed(capsqlalchemy, db_engine):
            async with db_engine.connect() as conn:
                await conn.execute(text("SELECT 1"))

            capsqlalchemy.assert_query_count(1, include_tcl=False)
    """)

    result = pytester.runpytest()

    result.assert_outcomes(passed=3)
