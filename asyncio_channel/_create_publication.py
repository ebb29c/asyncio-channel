__all__ = ('create_publication',)

from asyncio import create_task

from ._create_channel import create_channel
from ._create_multiple import create_multiple
from ._mixin import ReprMixin


async def _start(src, get_topic, topics, notify):
    """Takes items and put on topic channel."""
    async for x in src:
        topic = get_topic(x)
        out = topics.get(topic)

        if out is not None:
            await out.put(x)

    notify()


class Publication(ReprMixin):
    """Get a publication of the src channel.

    Items will be assigned a topic by the supplied topic_fn and then
    distributed to all channels subscribed to that topic.  If a topic
    has no subscribed channels then the item is dropped.
    """

    def __init__(self, src, topic_fn, *, n_or_buffer=1,
                 _create_task=create_task):
        self._n_or_buffer = n_or_buffer
        self._mults = {}
        self._topics = topics = {}
        _create_task(_start(src, topic_fn, topics, self._notify))

    def subscribe(self, topic, ch, *, close=True,
                  _create_channel=create_channel,
                  _create_multiple=create_multiple):
        """Subscribe channel to topic.

        If close is True then the channel will be closed when the
        publication is closed.
        """
        topics = self._topics
        if topics is None:
            return

        if topic not in topics:
            src = _create_channel(self._n_or_buffer)
            topics[topic] = src

            m = create_multiple(src)
            self._mults[topic] = m

        self._mults[topic].add_output(ch, close=close)

    def unsubscribe(self, topic, ch):
        """Unsubscribe channel from topic."""
        topics = self._topics
        if topics and topic in topics:
            self._mults[topic].remove_output(ch)

    def unsubscribe_all(self, topic=None):
        """Unsubscribe all channels, or just for a single topic."""
        topics = self._topics
        if topics is None:
            return

        if topic is None:
            for m in self._mults.values():
                m.remove_all_outputs()
        elif topic in topics:
            self._mults[topic].remove_all_outputs()

    def _notify(self):
        topics = self._topics
        mults = self._mults

        for src in topics.values():
            src.close()

        topics.clear()
        mults.clear()
        self._topics = None
        self._mults = None

    def _format(self):
        return 'done' if self._topics is None else 'active'


create_publication = Publication
