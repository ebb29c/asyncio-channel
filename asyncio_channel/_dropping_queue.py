from __future__ import annotations

__all__ = ('DroppingQueue',)

from typing import Any

from ._types import BufferProtocol


class DroppingQueue:
    """A queue adapter that maintains a "fixed window".

    When an item is added to a full queue, instead of blocking it is
    discarded.
    """

    def __init__(self, queue: BufferProtocol) -> None:
        self.empty = queue.empty
        self.join = queue.join  # type: ignore[attr-defined]
        self.maxsize = queue.maxsize
        self.qsize = queue.qsize
        self.task_done = queue.task_done  # type: ignore[attr-defined]
        self.get_nowait = queue.get_nowait
        self.get = queue.get

        self._full = queue.full
        self._put_nowait = queue.put_nowait
        self._put = queue.put

    def full(self) -> bool:
        """Return True if "put" will block, False otherwise."""
        return False

    def put_nowait(self, x: Any) -> None:
        """Synchronously add x to the queue.

        May drop x.
        """
        if not self._full():
            self._put_nowait(x)

    async def put(self, x: Any) -> None:
        """Asynchronously add x to the queue.

        Calls put_nowait.
        """
        self.put_nowait(x)
