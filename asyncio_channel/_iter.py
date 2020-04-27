__all__ = ('itermerge', 'iterzip')

from asyncio import create_task
from itertools import chain

from ._util import wait_all, wait_first

SENTINEL = object()


class MergeIterator:
    """Get an asynchronous iterator.

    .__anext__() will return the next item available on any channel.
    If more than one channel has an item, then a non-deterministic
    selection will be made.

    Iteration is stopped when all channels are closed.
    """

    def __init__(self, *chs):
        self._chs = chs

    def __aiter__(self):
        return self

    async def __anext__(self, *,
                        _chain=chain,
                        _create_task=create_task,
                        _sentinel=SENTINEL,
                        _wait_first=wait_first,):
        tasks = []
        task_to_ch = {}
        add_task = tasks.append
        for ch in self._chs:
            task = _create_task(ch.item())
            task_to_ch[id(task)] = ch
            add_task(task)

        done, pending = await _wait_first(*tasks)

        x = _sentinel
        next_chs = []
        add_to_next = next_chs.append
        for task in _chain(done, pending):
            ch = task_to_ch[id(task)]
            if task in done:
                if not task.result():
                    # Associated channel is closed, so drop it from
                    # the next iteration.
                    continue
                if x is _sentinel:
                    # Store the first available item for return.
                    x = ch.poll()
            add_to_next(ch)

        if x is _sentinel:
            # Didn't find an item, so stop.
            raise StopAsyncIteration
        return x


itermerge = MergeIterator


class ZipIterator:
    """Get an asynchronous zip object.

    The i-th .__anext__() call will return a tuple of the i-th item
    taken from each channel.  Each item's index within the tuple will
    match the index of the channel in the zip() argument list from
    which it was taken.

    Iteration is stopped when any channel is closed.
    """

    def __init__(self, *chs):
        self._chs = chs

    def __aiter__(self):
        return self

    async def __anext__(self, *,
                        _create_task=create_task,
                        _wait_all=wait_all,
                        _wait_first=wait_first):
        """Return a tuple with the next items from each channel."""
        chs = self._chs

        closed_coro = _wait_first(*(ch.closed() for ch in chs))
        closed_task = _create_task(closed_coro)
        # Wait for one of the following:
        done, _ = await _wait_first(
            # 1. Any channel is closed.
            closed_task,
            # 2. All channels contain an item.
            _wait_all(*(ch.item() for ch in chs)))

        if closed_task in done:
            raise StopAsyncIteration

        return tuple(ch.poll() for ch in chs)


iterzip = ZipIterator
