from asyncio_channel import create_channel, onto_channel, reduce, \
                            set_exception_handler
from asyncio_channel._util import _default_exception_handler

import asyncio
import operator


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

async def test_reduce_empty_input_no_init():
    """
    GIVEN
        reduce() with the default init of None.
    WHEN
        The input channel closes without yielding any items.
    EXPECT
        The result channel closes cleanly; no exception is forwarded to
        the exception handler (putting None on a channel is invalid).
    """
    errors = []
    set_exception_handler(lambda exc, task: errors.append(exc))
    try:
        ch = create_channel()
        out = reduce(operator.add, ch)
        ch.close()
        await asyncio.wait_for(out.closed(), timeout=1.0)
        assert await out.take(timeout=0.05) is None
        # Let the background task finish and its done-callback run.
        for _ in range(5):
            await asyncio.sleep(0)
        assert not errors
    finally:
        set_exception_handler(_default_exception_handler)
