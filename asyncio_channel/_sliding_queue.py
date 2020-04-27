__all__ = ('SlidingQueue',)


class SlidingQueue:
    """A queue adapter that maintains a "sliding window".

    When an item is added to a full queue, instead of blocking the oldest
    item in the queue is discarded.
    """

    def __init__(self, queue):
        self.empty = queue.empty
        self.join = queue.join
        self.maxsize = queue.maxsize
        self.qsize = queue.qsize
        self.task_done = queue.task_done
        self.get_nowait = queue.get_nowait
        self.get = queue.get

        self._full = queue.full
        self._put_nowait = queue.put_nowait
        self._put = queue.put

    def full(self):
        """Return True if "put" will block, False otherwise."""
        return False

    def put_nowait(self, x):
        """Synchronously add x to the queue.

        May discard the oldest item from the queue.
        """
        if self._full():
            self.get_nowait()
        self._put_nowait(x)

    async def put(self, x):
        """Asynchronously add x to the queue.

        Calls put_nowait.
        """
        self.put_nowait(x)
