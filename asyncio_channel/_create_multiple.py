__all__ = ('create_multiple',)

from asyncio import create_task

from ._mixin import ReprMixin
from ._util import wait_all


async def _put(ch, x):
    if ch.full():
        await ch.put(x)
    else:
        ch.offer(x)


async def _start(src, outs, done, _put=_put, _wait_all=wait_all):
    while True:
        if not await src.item():
            break

        x = src.poll()
        await wait_all(*(_put(ch, x) for ch, _ in outs))

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

    def __init__(self, src, *,
                 _start=_start, _create_task=create_task):
        self._outs = outs = []
        self._done = False
        _create_task(_start(src, outs, self._notify))

    def add_output(self, ch, *, close=True):
        """In the future, copy items put on src to ch.

        If close is True then ch will be closed when src is closed.

        Return True if the output channel is added, False otherwise.
        """
        if self._done:
            return False

        self._outs.append((ch, close))
        return True

    def remove_output(self, ch):
        """No longer copy items put on src to ch."""
        outs = self._outs
        for i, out in enumerate(outs):
            out_ch, _ = out
            if ch is out_ch:
                del outs[i]
                break

    def remove_all_outputs(self):
        """Remove all output channels."""
        self._outs.clear()

    def _notify(self):
        self._done = True

    def _format(self):
        return 'done' if self._done else 'active'


create_multiple = ChannelMultiple
