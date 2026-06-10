from asyncio_channel import create_channel, create_mix

import asyncio
import pytest
import re


async def test_mix_property():
    """
    GIVEN
        A mix.
    WHEN
        Set and get the 'priority_mode' property.
    EXPECT
        Able to set and get the mode.
    """
    ch = create_channel()
    m = create_mix(ch)
    assert m.priority_mode == m.PRIORITY_OFF
    m.priority_mode = m.PRIORITY_MUTE
    assert m.priority_mode == m.PRIORITY_MUTE
    m.priority_mode = m.PRIORITY_PAUSE
    assert m.priority_mode == m.PRIORITY_PAUSE
    ch.close()
    await asyncio.sleep(0.05)

async def test_mix_property_invalid():
    """
    GIVEN
        A mix.
    WHEN
        Assign invalid value to 'priority_mode' property.
    EXPECT
        Raises ValueError.
    """
    ch = create_channel()
    m = create_mix(ch)
    with pytest.raises(ValueError, match='invalid priority mode'):
        m.priority_mode = 'foo'
    ch.close()
    await asyncio.sleep(0.05)

async def test_mix():
    """
    GIVEN
        A mix, in non-priority mode, with two input channels.
    WHEN
        An item is added to each input channel.
    EXPECT
        All items are transfered to output channel.
    """
    ch1 = create_channel()
    ch2 = create_channel()
    out = create_channel()
    m = create_mix(out)
    m.add_input(ch1)
    m.add_input(ch2)
    a = 'a'
    b = 'b'
    assert ch1.offer(a)
    assert ch2.offer(b)
    x = await out.take(timeout=0.05)
    y = await out.take(timeout=0.05)
    assert not frozenset((x, y)).difference((a, b))
    out.close()
    await asyncio.sleep(0.05)

async def test_mix_unmix():
    """
    GIVEN
        A mix, in non-priority mode, with two input channels.
    WHEN
        One input channel is unmix'd.
    EXPECT
        Item from the unmix'd channel is not taken.
    """
    ch1 = create_channel()
    ch2 = create_channel()
    out = create_channel()
    m = create_mix(out)
    m.add_input(ch1)
    m.add_input(ch2)
    a = 'a'
    b = 'b'
    assert ch1.offer(a)
    assert ch2.offer(b)
    m.remove_input(ch2)
    x = await out.take(timeout=0.05)
    assert x == a
    assert await out.take(timeout=0.05) is None
    assert not ch2.empty()
    out.close()
    await asyncio.sleep(0.05)

async def test_mix_mute():
    """
    GIVEN
        A mix, in non-priority mode, with two input channels, one muted.
    WHEN
        An item is added to each input channel.
    EXPECT
        Item from non-muted channel is put on output channel.  Item from
        muted channel is taken but not put on output channel.
    """
    ch1 = create_channel()
    ch2 = create_channel()
    out = create_channel()
    m = create_mix(out)
    m.add_input(ch1)
    m.toggle(ch1, {},
             ch2, {'mute': True})
    a = 'a'
    b = 'b'
    assert ch1.offer(a)
    assert ch2.offer(b)
    x = await out.take(timeout=0.05)
    assert x == a
    assert out.empty()
    assert ch2.empty()
    out.close()
    await asyncio.sleep(0.05)

async def test_mix_pause():
    """
    GIVEN
        A mix, in non-priority mode, with two input channel, one paused.
    WHEN
        An item is added to each input channel.
    EXPECT
        Item from non-paused channel is put on output channel.  Item from
        paused channel is not taken.
    """
    ch1 = create_channel()
    ch2 = create_channel()
    out = create_channel()
    m = create_mix(out)
    m.add_input(ch1)
    m.toggle(ch1, {},
             ch2, {'pause': True})
    a = 'a'
    b = 'b'
    assert ch1.offer(a)
    assert ch2.offer(b)
    x = await out.take(timeout=0.05)
    assert x == a
    assert out.empty()
    assert await out.take(timeout=0.05) is None
    assert not ch2.empty()
    out.close()
    await asyncio.sleep(0.05)

async def test_mix_priority_mute():
    """
    GIVEN
        A mix, in priority-mode=mute, with two input channels,
        one with priority.
    WHEN
        An item is added to each input channel.
    EXPECT
        Item from priority channel is put on output channel.  Item
        from non-priority channel is taken but not put on output
        channel.
    """
    ch1 = create_channel()
    ch2 = create_channel()
    out = create_channel()
    m = create_mix(out)
    m.priority_mode = m.PRIORITY_MUTE
    m.add_input(ch1)
    m.toggle(ch1, {},
             ch2, {'priority': True})
    a = 'a'
    b = 'b'
    assert ch1.offer(a)
    assert ch2.offer(b)
    x = await out.take(timeout=0.05)
    assert x == b
    assert out.empty()
    assert ch1.empty()
    out.close()
    await asyncio.sleep(0.05)

async def test_mix_priority_pause():
    """
    GIVEN
        A mix, in priority-mode=pause, with two input channels,
        one with priority.
    WHEN
        An item is added to each input channel.
    EXPECT
        Item from priority channel is put on output channel.  Item
        from non-priority channel is not taken.
    """
    ch1 = create_channel()
    ch2 = create_channel()
    out = create_channel()
    m = create_mix(out)
    m.priority_mode = m.PRIORITY_PAUSE
    m.add_input(ch1)
    m.toggle(ch1, {},
             ch2, {'priority': True})
    a = 'a'
    b = 'b'
    assert ch1.offer(a)
    assert ch2.offer(b)
    x = await out.take(timeout=0.05)
    assert x == b
    assert out.empty()
    assert await out.take(timeout=0.05) is None
    assert not ch1.empty()
    out.close()
    await asyncio.sleep(0.05)

async def test_mix_remove_all_inputs():
    """
    GIVEN
        A max, in non-priority mode, with two input channels.
    WHEN
        All inputs are removed.
    EXPECT
        Items put on input channels are not taken.
    """
    ch1 = create_channel()
    ch2 = create_channel()
    out = create_channel()
    m = create_mix(out)
    m.add_input(ch1)
    m.add_input(ch2)
    m.remove_all_inputs()
    assert ch1.offer('a')
    assert ch2.offer('b')
    assert await out.take(timeout=0.05) is None
    assert not ch1.empty()
    assert not ch2.empty()
    out.close()
    await asyncio.sleep(0.05)

async def test_mix_toggle_error_cases():
    """
    WHEN
        Call toggle with invalid arguments.
    EXPECT
        Errors to be raised.
    """
    out = create_channel()
    m = create_mix(out)
    with pytest.raises(ValueError, match='no arguments'):
        m.toggle()

    with pytest.raises(ValueError, match='odd number of arguments'):
        m.toggle(1)

    ch = create_channel()
    with pytest.raises(TypeError,
            match='argument 2 must be a channel, not a str'):
        m.toggle(ch, {}, '', {})

    with pytest.raises(TypeError,
            match='argument 1 must be a dict, not a str'):
        m.toggle(ch, '')

    with pytest.raises(KeyError,
            match='argument 1 contains keys bar, foo, only '
                  'mute, pause, priority are allowed'):
        m.toggle(ch, {'mute': True, 'foo': False, 'bar': True})

    out.close()
    await asyncio.sleep(0.05)

async def test_mix_restart():
    """
    GIVEN
        A mix with two input channels.
    WHEN
        An item is added to one input channel, but the channel is
        removed from the mix before the item can be taken.
    EXPECT
        Item to not be taken from input channel.
    """
    out = create_channel(10)
    m = create_mix(out)
    ch1 = create_channel()
    ch2 = create_channel()
    m.toggle(ch1, {}, ch2, {})
    # Confirm the mix is running by waiting for it to transfer a warmup item.
    ch2.offer('warmup')
    assert await out.take(timeout=1.0) == 'warmup'
    assert ch1.offer('a')
    # ch1 is part of the current mix, removing it is expected to
    # reset the take operation.
    m.remove_input(ch1)
    assert await out.take(timeout=0.5) is None
    assert not ch1.empty()
    out.close()

async def test_mute_restart():
    """
    GIVEN
        A mix with two muted input channels.
    WHEN
        An item is added to one input channel, but the channel is
        removed from the mix before the item can be taken.
    EXPECT
        Item to not be taken from input channel.
    """
    out = create_channel()
    m = create_mix(out)
    ch1 = create_channel()
    ch2 = create_channel()
    m.toggle(ch1, {'mute': True}, ch2, {'mute': True})
    # offer and remove_input are both synchronous, so they happen atomically
    # from the event loop's perspective — the drain loop cannot process ch1
    # between the two calls.
    assert ch1.offer('a')
    m.remove_input(ch1)
    assert await out.take(timeout=0.5) is None
    assert not ch1.empty()
    out.close()

async def test_toggle_preserves_unmentioned_channels():
    """
    GIVEN
        A mix with two input channels.
    WHEN
        toggle() is called with only one of them.
    EXPECT
        The other channel is still active in the mix.
    """
    out = create_channel(10)
    m = create_mix(out)
    ch1 = create_channel()
    ch2 = create_channel()
    m.add_input(ch1)
    m.add_input(ch2)
    # Toggle only ch1 — ch2 must remain in the mix unchanged.
    m.toggle(ch1, {'mute': True})
    # Items on ch2 should still flow to out.
    assert ch2.offer('from-ch2')
    result = await out.take(timeout=1.0)
    assert result == 'from-ch2'
    out.close()
    await asyncio.wait_for(out.closed(), timeout=1.0)


async def test_mix_round_robin_fairness():
    """
    GIVEN
        A mix with two input channels, both holding several items.
    WHEN
        Items are transferred to the output channel.
    EXPECT
        Items are taken from the input channels in alternation rather
        than draining the first channel before reading the second.
    """
    out = create_channel(10)
    m = create_mix(out)
    ch1 = create_channel(3)
    ch2 = create_channel(3)
    for i in range(3):
        assert ch1.offer(f'a{i}')
        assert ch2.offer(f'b{i}')
    m.toggle(ch1, {}, ch2, {})
    items = [await out.take(timeout=1.0) for _ in range(6)]
    assert None not in items
    # The first two transfers must come from different channels.
    assert {items[0][0], items[1][0]} == {'a', 'b'}
    # And reads must alternate throughout.
    sources = [x[0] for x in items]
    assert sources[0::2] != sources[1::2]
    assert sorted(items) == ['a0', 'a1', 'a2', 'b0', 'b1', 'b2']
    out.close()

async def test_mix_no_item_loss_when_out_refills():
    """
    GIVEN
        A mix whose out channel regained capacity, then was filled by
        another producer before any input received an item.
    WHEN
        An item arrives on an input channel.
    EXPECT
        The item is not lost; it is transferred once out has capacity
        again.
    """
    out = create_channel()
    m = create_mix(out)
    ch = create_channel()
    m.add_input(ch)
    # Let the mix task enter its wait so out.capacity() has already
    # completed (out is empty at this point).  The mix's wait chain is
    # several tasks deep, so yield enough times for it to settle.
    for _ in range(10):
        await asyncio.sleep(0)
    # Fill out from elsewhere, then satisfy the ch.item() wait.
    assert out.offer('blocker')
    assert ch.offer('x')
    # Let the mix task wake and run its loop body while out is full.
    for _ in range(10):
        await asyncio.sleep(0)
    assert await out.take(timeout=1.0) == 'blocker'
    # The polled item must not have been dropped on a failed offer.
    assert await out.take(timeout=1.0) == 'x'
    assert ch.empty()
    out.close()

async def test_mix_prunes_closed_input():
    """
    GIVEN
        A mix with two input channels.
    WHEN
        One input channel is closed (but not removed from the mix).
    EXPECT
        The closed channel is pruned from the wait list, so the mix
        does not busy-spin, and the remaining input keeps working.
    """
    out = create_channel(10)
    m = create_mix(out)
    ch1 = create_channel()
    ch2 = create_channel()
    m.toggle(ch1, {}, ch2, {})
    ch1.close()
    # Let the mix task wake on the closed channel and prune it.
    for _ in range(10):
        await asyncio.sleep(0)
    assert ch1 not in m._mix
    assert ch2 in m._mix
    assert ch2.offer('x')
    assert await out.take(timeout=1.0) == 'x'
    out.close()

async def test_drain_prunes_closed_input():
    """
    GIVEN
        A mix with two muted input channels.
    WHEN
        One muted channel is closed (but not removed from the mix).
    EXPECT
        The closed channel is pruned from the drain wait list, so the
        drain task does not busy-spin, and the other muted channel is
        still drained.
    """
    out = create_channel(10)
    m = create_mix(out)
    ch1 = create_channel()
    ch2 = create_channel()
    m.toggle(ch1, {'mute': True}, ch2, {'mute': True})
    ch1.close()
    # Let the drain task wake on the closed channel and prune it.
    for _ in range(10):
        await asyncio.sleep(0)
    assert ch1 not in m._mute
    assert ch2 in m._mute
    assert ch2.offer('x')
    # Muted items are taken but not forwarded.
    for _ in range(10):
        await asyncio.sleep(0)
    assert ch2.empty()
    assert out.empty()
    out.close()

async def test_priority_mode_transitions():
    """
    GIVEN
        A mix with one priority channel and one normal channel.
    WHEN
        priority_mode is changed between all three modes while items are active.
    EXPECT
        Items follow the new mode's routing rules after each transition.
    """
    out = create_channel(10)
    m = create_mix(out)
    ch_pri = create_channel()
    ch_norm = create_channel()
    m.toggle(ch_pri, {'priority': True}, ch_norm, {})

    # PRIORITY_MUTE: only priority channel forwarded
    m.priority_mode = m.PRIORITY_MUTE
    assert ch_pri.offer('p1')
    assert await out.take(timeout=1.0) == 'p1'

    # PRIORITY_PAUSE: priority forwarded, non-priority not taken
    m.priority_mode = m.PRIORITY_PAUSE
    assert ch_norm.offer('n2')
    assert ch_pri.offer('p2')
    assert await out.take(timeout=1.0) == 'p2'
    assert await out.take(timeout=0.1) is None
    assert not ch_norm.empty()
    ch_norm.poll()  # clear before PRIORITY_OFF step

    # PRIORITY_OFF: both channels forwarded
    m.priority_mode = m.PRIORITY_OFF
    assert ch_pri.offer('p3')
    assert ch_norm.offer('n3')
    received = {await out.take(timeout=1.0), await out.take(timeout=1.0)}
    assert received == {'p3', 'n3'}

    out.close()

async def test_mix_empty_mute_list_no_crash():
    """
    GIVEN
        A mix in PRIORITY_PAUSE mode with no muted channels.
    WHEN
        The mix is running.
    EXPECT
        No ValueError from calling wait_first() with zero arguments.
    """
    out = create_channel(10)
    m = create_mix(out)
    ch = create_channel()
    m.toggle(ch, {'priority': True})
    m.priority_mode = m.PRIORITY_PAUSE
    # With PRIORITY_PAUSE, only priority channels go to mix; mute list is
    # empty.  Putting an item should reach out without crashing.
    assert ch.offer('ok')
    result = await out.take(timeout=1.0)
    assert result == 'ok'
    out.close()
    await asyncio.wait_for(out.closed(), timeout=1.0)
