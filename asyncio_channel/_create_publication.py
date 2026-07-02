from __future__ import annotations

__all__ = ('create_publication',)

from asyncio import Task, create_task
from collections.abc import Callable
from typing import Any

from ._channel import Channel
from ._create_channel import create_channel
from ._create_multiple import create_multiple, ChannelMultiple
from ._mixin import ReprMixin
from ._types import BufferProtocol, ReadableChannel, WritableChannel
from ._util import _task_done_callback


async def _start(src: ReadableChannel,
                 get_topic: Callable[[Any], Any],
                 topics: dict[Any, Channel],
                 notify: Callable[[], None],
                 ) -> None:
    """Takes items and put on topic channel."""
    try:
        async for x in src:
            topic = get_topic(x)
            out = topics.get(topic)

            if out is not None:
                await out.put(x)
    except Exception:
        notify()
        raise

    notify()


class Publication(ReprMixin):
    """Get a publication of the src channel.

    Items will be assigned a topic by the supplied topic_fn and then
    distributed to all channels subscribed to that topic.  If a topic
    has no subscribed channels then the item is dropped.
    """

    def __init__(self, src: ReadableChannel,
                 topic_fn: Callable[[Any], Any], *,
                 buffer: int | BufferProtocol = 1,
                 _create_task: Callable[..., Task[Any]] = create_task,
                 _task_done_callback: Callable[[Task[Any]], None] = _task_done_callback,
                 ) -> None:
        self._buffer = buffer
        self._mults: dict[Any, ChannelMultiple] = {}
        topics: dict[Any, Channel] = {}
        self._topics: dict[Any, Channel] | None = topics
        task = _create_task(_start(src, topic_fn, topics, self._notify))
        task.add_done_callback(_task_done_callback)

    def subscribe(self, topic: Any, ch: WritableChannel, *, close: bool = True,
                  _create_channel: Callable[
                      [int | BufferProtocol], Channel] = create_channel,
                  _create_multiple: Callable[
                      [ReadableChannel], ChannelMultiple] = create_multiple,
                  ) -> None:
        """Subscribe channel to topic.

        If close is True then the channel will be closed when the
        publication is closed.
        """
        topics = self._topics
        if topics is None:
            return

        if topic not in topics:
            src = _create_channel(self._buffer)
            topics[topic] = src

            m = _create_multiple(src)
            self._mults[topic] = m

        self._mults[topic].add_output(ch, close=close)

    def unsubscribe(self, topic: Any, ch: WritableChannel) -> None:
        """Unsubscribe channel from topic."""
        topics = self._topics
        if topics and topic in topics:
            self._mults[topic].remove_output(ch)

    def unsubscribe_all(self, topic: Any = None) -> None:
        """Unsubscribe all channels, or just for a single topic."""
        topics = self._topics
        if topics is None:
            return

        if topic is None:
            for m in self._mults.values():
                m.remove_all_outputs()
        elif topic in topics:
            self._mults[topic].remove_all_outputs()

    def _notify(self) -> None:
        topics = self._topics
        mults = self._mults

        for src in topics.values():
            src.close()

        topics.clear()
        mults.clear()
        self._topics = None
        self._mults = None

    def _format(self) -> str:
        return 'done' if self._topics is None else 'active'


create_publication = Publication
