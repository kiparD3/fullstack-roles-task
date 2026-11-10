import pytest


@pytest.fixture(scope="session", autouse=True)
def db():
    """Override the integration fixture: unit tests must not open a database."""
    yield None
