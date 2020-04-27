from asyncio_channel import create_channel, create_publication

import asyncio
import operator
import pytest


@pytest.mark.asyncio
async def test_publication():
    """
    GIVEN
        Two topics with subscribed channels.  Only one channel set to
        close when src channel closes.
    WHEN
        An item is put on src channel.
    EXPECT
        Item is put on topic channel. Subscribed channels are closed
        when src channel is closed.
    """
    src = create_channel()
    get_type = operator.itemgetter('type')
    p = create_publication(src, get_type)
    a_ch = create_channel()
    p.subscribe('a', a_ch)
    b_ch = create_channel()
    p.subscribe('b', b_ch, close=False)
    x = {'type': 'b', 'value': 42}
    assert src.offer(x)
    r = await b_ch.take(timeout=0.05)
    assert r is x
    assert a_ch.empty()
    src.close()
    await asyncio.sleep(0.05)
    assert a_ch.is_closed()
    assert not b_ch.is_closed()

@pytest.mark.asyncio
async def test_publication_unsubscribe():
    """
    GIVEN
        Two topics with subscribed channels.
    WHEN
        A channel is unsubscribed then an item is put on src channel.
    EXPECT
        Item is put on subscribed topic channels, but not the
        unsubscribed channel.
    """
    src = create_channel()
    get_type = operator.itemgetter('type')
    p = create_publication(src, get_type)
    a_ch = create_channel()
    p.subscribe('a', a_ch)
    b_ch = create_channel()
    p.subscribe('b', b_ch)
    b2_ch = create_channel()
    p.subscribe('b', b2_ch)
    p.unsubscribe('b', b_ch)
    x = {'type': 'b', 'value': 42}
    assert src.offer(x)
    r = await b2_ch.take(timeout=0.05)
    assert r is x
    assert a_ch.empty()
    assert b_ch.empty()
    src.close()
    await asyncio.sleep(0.05)

@pytest.mark.asyncio
async def test_publication_unsubscribe_all():
    """
    GIVEN
        Two topics with subscribed channels.
    WHEN
        All channels are unsubscribed then an item is put on src channel.
    EXPECT
        The item is taken from src channel and dropped.
    """
    src = create_channel()
    get_type = operator.itemgetter('type')
    p = create_publication(src, get_type)
    a_ch = create_channel()
    p.subscribe('a', a_ch)
    b_ch = create_channel()
    p.subscribe('b', b_ch)
    p.unsubscribe_all()
    x = {'type': 'b', 'value': 42}
    assert src.offer(x)
    await asyncio.sleep(0.05)
    assert src.empty()
    assert a_ch.empty()
    assert b_ch.empty()
    src.close()
    await asyncio.sleep(0.05)

@pytest.mark.asyncio
async def test_publication_unsubscribe_all_on_topic():
    """
    GIVEN
        Two topics with subscribed channels.
    WHEN
        All channels are unsubscribed then an item is put on src channel.
    EXPECT
        The item is taken from src channel and dropped.
    """
    src = create_channel()
    get_type = operator.itemgetter('type')
    p = create_publication(src, get_type)
    a_ch = create_channel()
    p.subscribe('a', a_ch)
    b_ch = create_channel()
    p.subscribe('b', b_ch)
    b2_ch = create_channel()
    p.subscribe('b', b2_ch)
    p.unsubscribe_all('b')
    x = {'type': 'b', 'value': 42}
    assert src.offer(x)
    await asyncio.sleep(0.05)
    assert src.empty()
    assert a_ch.empty()
    assert b_ch.empty()
    assert b2_ch.empty()
    src.close()
    await asyncio.sleep(0.05)
