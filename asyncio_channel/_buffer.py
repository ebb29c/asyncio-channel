__all__ = (
    'create_blocking_buffer',
    'create_dropping_buffer',
    'create_sliding_buffer'
)

from asyncio import Queue

from ._dropping_queue import DroppingQueue
from ._sliding_queue import SlidingQueue


def create_blocking_buffer(n):
    """Get a buffer of size n.

    If buffer is full then attempts to add an item will block.
    """
    if not isinstance(n, int):
        raise TypeError(f'n must be an integer, not a {type(n)}')
    if n < 1:
        raise ValueError(f'n must be a positive integer, not {n}')
    return Queue(n)


def create_dropping_buffer(n):
    """Get a buffer of size n.

    If buffer is full then adding an item will not block, but the item
    will be discarded.
    """
    return DroppingQueue(create_blocking_buffer(n))


def create_sliding_buffer(n):
    """Get a buffer of size n.

    If buffer is full then adding an item will not block, but the oldest
    item in the buffer will be removed and discarded.
    """
    return SlidingQueue(create_blocking_buffer(n))
