import pytest

from asyncio_channel import create_channel


@pytest.fixture
def ch():
    """A single-item channel, closed after the test."""
    channel = create_channel()
    yield channel
    channel.close()


@pytest.fixture
def buffered_ch():
    """Factory fixture that creates a channel with an n-item buffer."""
    def _make(n: int):
        return create_channel(n)
    return _make
