__all__ = ('Channel',)

from asyncio import Event

from ._mixin import ReprMixin
from ._util import wait_first


class Channel(ReprMixin):
    """A channel, useful for coordinating producer and consumer coroutines.

    Similary to asyncio.Queue, but adds asynchronous iteration support and
    the ability to "close" a channel, thus preventing adding more items.
    """

    def __init__(self, queue, *, _Event=Event):
        self.empty = queue.empty
        self.full = queue.full
        self._get = queue.get
        self._get_nowait = queue.get_nowait
        self._put = queue.put
        self._put_nowait = queue.put_nowait
        self._size = queue.qsize
        self._maxsize = queue.maxsize

        closed = _Event()
        self.closed = closed.wait
        self.close = closed.set
        self.is_closed = closed.is_set

        self._capacity = _Event()
        self._item = _Event()

        self._update_state()

    async def capacity(self, *, timeout=None, _wait_first=wait_first):
        """Block until the channel has capacity or is closed.

        If timeout is an int or float then unblock after that time has
        elapse.

        Returns True if the channel is open and has capacity, otherwise
        False.
        """
        is_closed = self.is_closed
        full = self.full
        capacity = self._capacity.wait
        closed = self.closed

        # The capacity Event will wake all blocked coroutines.  If the
        # channel still has capacity when unblocked then return, otherwise
        # block again.  If the caller doesn't utilize the capacity then
        # the next unblocked coroutines will get a chance.
        while full() and not is_closed():
            done, _ = await _wait_first(capacity(), closed(),
                                        timeout=timeout)
            if not done:
                return False

        return not (full() or is_closed())

    async def item(self, *, timeout=None, _wait_first=wait_first):
        """Block until the channel has an item or is closed.

        If timeout is an int or float then unblock after that time has
        elapse.

        Returns True if the channel has an item, otherwise False.
        """
        empty = self.empty
        is_closed = self.is_closed
        item = self._item.wait
        closed = self.closed

        # The item Event will wake all blocked coroutines.  If the
        # channel still has an item when unblocked then return, otherwise
        # block again.  If the caller doesn't take the item then
        # the next unblocked coroutines will get a chance.
        while empty() and not is_closed():
            done, _ = await _wait_first(item(), closed(),
                                        timeout=timeout)
            if not done:
                return False

        return not empty()

    def offer(self, x):
        """Synchronously add x to the channel.

        Return True if x was added to the channel, False otherwise.

        Raises ValueError if offered None.
        """
        if x is None:
            raise ValueError('None is not allowed on channel')

        if self.is_closed() or self.full():
            return False

        self._put_nowait(x)
        self._update_state()
        return True

    def poll(self, *, default=None):
        """Synchronously get an item from the channel.

        Return an item, if available, or default.
        """
        if self.empty():
            return default

        x = self._get_nowait()
        self._update_state()
        return x

    async def put(self, x, *, timeout=None):
        """Asynchronously add x to the channel.

        Return True if x was added to the channel, False otherwise.

        Raises a ValueError if attempting to put None.
        """
        return (self.offer(x)
                or (await self.capacity(timeout=timeout)
                    and self.offer(x)))

    async def take(self, *, timeout=None, default=None):
        """Asynchronously get an item from the channel.

        Return an item, if available, otherwise block until an item becomes
        available.  Return default if timeout is given and has expired.
        """
        x = self.poll(default=default)
        if x is default and await self.item(timeout=timeout):
            x = self.poll(default=default)
        return x

    def _update_state(self):
        """Update waitable state flags."""
        if self.full():
            self._capacity.clear()
        else:
            self._capacity.set()

        if self.empty():
            self._item.clear()
        else:
            self._item.set()

    def __aiter__(self):
        """Return an asynchronous iterator."""
        return self

    async def __anext__(self):
        """Return the next item from the channel."""
        x = self.poll()
        if x is None:
            x = await self.take()

        if x is None:
            raise StopAsyncIteration

        return x

    def _format(self):
        return ' '.join((
            'closed' if self.is_closed() else 'open',
            f'items={self._size()}',
            f'max_capacity={self._maxsize}'
        ))
