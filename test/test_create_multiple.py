from asyncio_channel import create_channel, create_multiple

import asyncio
import pytest


@pytest.mark.asyncio
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
    await asyncio.sleep(0.05)
    ch = create_channel()
    assert not m.add_output(ch)

@pytest.mark.asyncio
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
    await asyncio.wait_for(out1.closed(), timeout=0.05)
    with pytest.raises(asyncio.TimeoutError):
        await asyncio.wait_for(out2.closed(), timeout=0.05)

@pytest.mark.asyncio
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
    await asyncio.sleep(0.05)
    m.remove_output(out1)
    x = 'x'
    src.offer(x)
    value2 = await out2.take(timeout=0.05)
    assert value2 == x
    assert out1.empty()
    src.close()
    await asyncio.wait_for(out2.closed(), timeout=0.05)
    with pytest.raises(asyncio.TimeoutError):
        await asyncio.wait_for(out1.closed(), timeout=0.05)

@pytest.mark.asyncio
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
    await asyncio.sleep(0.05)
    m.remove_all_outputs()
    x = 'x'
    src.offer(x)
    await asyncio.sleep(0.05)
    assert src.empty()
    assert out1.empty()
    assert out2.empty()
    src.close()
    await asyncio.sleep(0.05)

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
        def capture_exceptions(loop, context):
            exceptions.append(context['exception'])

        asyncio.get_running_loop().set_exception_handler(capture_exceptions)

        src = create_channel()
        mult = create_multiple(src)
        await src.put(42)
        await asyncio.sleep(0.05)
        assert src.empty()

        return exceptions

    exceptions = asyncio.run(start())
    assert not exceptions
