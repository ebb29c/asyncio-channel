from __future__ import annotations

__all__ = ('create_multiple',)

from asyncio import Task, create_task
from collections.abc import Callable, Coroutine
from typing import Any

from ._mixin import ReprMixin
from ._types import ReadableChannel, WritableChannel, _WaitFn
from ._util import _task_done_callback, wait_all


_PutFn = Callable[[WritableChannel, Any], Coroutine[Any, Any, None]]


async def _put(ch: WritableChannel, x: Any) -> None:
    if ch.full():
        await ch.put(x)
    else:
        ch.offer(x)


async def _start(src: ReadableChannel,
                 outs: list[tuple[WritableChannel, bool]],
                 done: Callable[[], None],
                 _put: _PutFn = _put,
                 _wait_all: _WaitFn = wait_all,
                 ) -> None:
    try:
        while True:
            if not await src.item():
                break

            x = src.poll()
            if outs:
                await _wait_all(*(_put(ch, x) for ch, _ in outs))
    except Exception:
        for ch, close in outs:
            if close:
                ch.close()
        done()
        raise

    # Close output channels.
    for ch, close in outs:
        if close:
            ch.close()

    done()  # Notify task complete.


class ChannelMultiple(ReprMixin):
    """Create a channel multiple.

    Items put on the input channel will be copied to all output channels.

    If no output channels are present then items put on input will be dropped.
    """

    def __init__(self, src: ReadableChannel, *,
                 _start: Callable[..., Coroutine[Any, Any, None]] = _start,
                 _create_task: Callable[..., Task[Any]] = create_task,
                 _task_done_callback: Callable[[Task[Any]], None] = _task_done_callback,
                 ) -> None:
        self._outs: list[tuple[WritableChannel, bool]] = []
        self._done = False
        task = _create_task(_start(src, self._outs, self._notify))
        task.add_done_callback(_task_done_callback)

    def add_output(self, ch: WritableChannel, *, close: bool = True) -> bool:
        """In the future, copy items put on src to ch.

        If close is True then ch will be closed when src is closed.

        Return True if the output channel is added, False otherwise.
        """
        if self._done:
            return False

        self._outs.append((ch, close))
        return True

    def remove_output(self, ch: WritableChannel) -> None:
        """No longer copy items put on src to ch."""
        outs = self._outs
        for i, out in enumerate(outs):
            out_ch, _ = out
            if ch is out_ch:
                del outs[i]
                break

    def remove_all_outputs(self) -> None:
        """Remove all output channels."""
        self._outs.clear()

    def _notify(self) -> None:
        self._done = True

    def _format(self) -> str:
        return 'done' if self._done else 'active'


create_multiple = ChannelMultiple
