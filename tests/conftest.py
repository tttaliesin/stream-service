import pytest


@pytest.fixture
def anyio_backend():
    """pytest-asyncio 설정"""
    return "asyncio"


@pytest.fixture(autouse=True)
def setup_logging():
    """테스트용 로깅 설정"""
    import logging
    logging.basicConfig(level=logging.DEBUG)