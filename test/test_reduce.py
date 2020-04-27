from asyncio_channel import create_channel, onto_channel, reduce

import asyncio
import operator
import pytest


@pytest.mark.asyncio
async def test_reduce():
    """
    EXPECT
        The result put on the output channel.
    """
    ch = create_channel()
    onto_channel(range(4), ch)
    out = reduce(operator.add, ch, init=0)
    result = await out.take(timeout=0.05)
    assert result == 6
    assert out.empty()
