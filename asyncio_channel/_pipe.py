__all__ = ('pipe',)

from asyncio import create_task

from ._util import wait_all


async def _pipe(src, dest, close, _wait_all=wait_all):
    """Transfer items from src to dest."""
    while True:
        await _wait_all(src.item(), dest.capacity())

        if src.empty() or dest.is_closed():
            break

        x = src.poll()
        dest.offer(x)

    if close and src.is_closed():
        dest.close()


def pipe(src, dest, *, close=True,
         _create_task=create_task, _pipe=_pipe):
    """Transfer items from src to dest.

    When src is closed, and "close" is True, then dest will be closed.
    """
    _create_task(_pipe(src, dest, close))
