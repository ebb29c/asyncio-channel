from asyncio_channel import create_channel, create_multiple

import asyncio
import pytest


async def test_multiple_closed():
    """
    GIVEN
        Closed multiple.
    WHEN
        Channel is added to ChannelMultiple.
    EXPECT
        Return False.
    """
    src = create_channel()
    src.close()
    m = create_multiple(src)
    # Add a sentinel output so we can detect when the background task has
    # finished (it closes all outputs when src is exhausted).
    sentinel = create_channel()
    m.add_output(sentinel)
    await asyncio.wait_for(sentinel.closed(), timeout=1.0)
    ch = create_channel()
    assert not m.add_output(ch)

async def test_add_output():
    """
    GIVEN
        ChannelMultiple with multiple output channels.
    WHEN
        Item is put on src channel.
    EXPECT
        Item is put on all output channels.
    """
    src = create_channel()
    out1 = create_channel()
    out2 = create_channel()
    m = create_multiple(src)
    assert m.add_output(out1)
    assert m.add_output(out2, close=False)
    x = 'x'
    src.offer(x)
    value1 = await out1.take(timeout=0.05)
    value2 = await out2.take(timeout=0.05)
    assert value1 == x
    assert value2 == x
    src.close()
    await asyncio.wait_for(out1.closed(), timeout=1.0)
    with pytest.raises(asyncio.TimeoutError):
        await asyncio.wait_for(out2.closed(), timeout=0.05)

async def test_remove_output():
    """
    GIVEN
        ChannelMultiple with multiple output channels.
    WHEN
        Output channel is removed then a item is put on src channel.
    EXPECT
        Item to not be copied to removed channel.
    """
    src = create_channel()
    out1 = create_channel()
    out2 = create_channel()
    m = create_multiple(src)
    assert m.add_output(out1)
    assert m.add_output(out2)
    # remove_output is synchronous; since no yield has occurred yet the
    # background task hasn't run, so it will see the updated output list.
    m.remove_output(out1)
    x = 'x'
    src.offer(x)
    value2 = await out2.take(timeout=0.05)
    assert value2 == x
    assert out1.empty()
    src.close()
    await asyncio.wait_for(out2.closed(), timeout=1.0)
    with pytest.raises(asyncio.TimeoutError):
        await asyncio.wait_for(out1.closed(), timeout=0.05)

async def test_remove_all_outputs():
    """
    GIVEN
        ChannelMultiple with multiple output channels.
    WHEN
        All output channels are removed then a item is put on src channel.
    EXPECT
        Item is not copied to former output channels, but is removed from
        src channel.
    """
    src = create_channel()
    out1 = create_channel()
    out2 = create_channel()
    m = create_multiple(src)
    assert m.add_output(out1)
    assert m.add_output(out2)
    m.remove_all_outputs()
    x = 'x'
    src.offer(x)
    src.close()
    # Add a sentinel output (before any yield) so we can detect when
    # the background task finishes.  The task hasn't run yet so sentinel
    # will be closed when the task exits.
    sentinel = create_channel()
    m.add_output(sentinel)
    await asyncio.wait_for(sentinel.closed(), timeout=1.0)
    assert src.empty()
    assert out1.empty()
    assert out2.empty()

def test_input_has_item_no_outputs():
    """
    See https://github.com/ebb29c/asyncio-channel/issues/1

    GIVEN
        A ChannelMultiple with no output channels.
    WHEN
        An item is put on the input channel.
    EXPECT
        The item is removed from the input channel and no error is raised.
    """
    async def start():
        exceptions = []
        asyncio.get_running_loop().set_exception_handler(
            lambda loop, ctx: exceptions.append(ctx['exception']))

        src = create_channel()
        mult = create_multiple(src)
        await src.put(42)
        src.close()
        # Add a sentinel output (before any yield) so we can detect when
        # the background task has finished.  The task hasn't run yet and
        # will close sentinel when src is exhausted.
        sentinel = create_channel()
        mult.add_output(sentinel)
        await asyncio.wait_for(sentinel.closed(), timeout=1.0)
        assert src.empty()
        return exceptions

    exceptions = asyncio.run(start())
    assert not exceptions
