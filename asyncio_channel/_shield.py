__all__ = ('ProhibitedOperationError', 'shield_from_close',
           'shield_from_read', 'shield_from_write')

from ._channel import Channel
from ._mixin import ReprMixin


class ProhibitedOperationError(Exception):
    pass


def _delegate_methods(receiver, target):
    """Delegate target's public methods to receiver."""
    receiver_methods = frozenset(dir(receiver))
    target_methods = frozenset(dir(target))

    forward_methods = target_methods.difference(receiver_methods)
    for method in forward_methods:
        if not method.startswith('_'):
            ref = getattr(target, method)
            setattr(receiver, method, ref)


class ChannelDecoratorBase(ReprMixin):

    def __init__(self, channel, *, silent=False):
        if not isinstance(channel, (Channel, ChannelDecoratorBase)):
            raise TypeError(
                f'must be a channel, not a {type(channel).__name__}')
        self._channel = channel
        self._silent = silent

    def _format(self):
        return f'channel={self._channel!r}'


class CloseShield(ChannelDecoratorBase):
    """Shield a channel from being closed.

    If silent is false then calling .close() will raise a
    ProhibitedOperationError.
    """

    def __init__(self, channel, *, silent=False,
                 _delegate_methods=_delegate_methods):
        super().__init__(channel, silent=silent)
        _delegate_methods(receiver=self, target=channel)

    def close(self):
        if not self._silent:
            raise ProhibitedOperationError('close')


shield_from_close = CloseShield


class ReadShield(ChannelDecoratorBase):
    """Shield a channel from having items read.

    If silent is false then calling .item(), .poll(), or
    .take() will raise a ProhibitedOperationError.
    """

    def __init__(self, channel, *, silent=False,
                 _delegate_methods=_delegate_methods):
        super().__init__(channel, silent=silent)
        _delegate_methods(receiver=self, target=channel)

    async def item(self, *, timeout=None):
        if not self._silent:
            raise ProhibitedOperationError('item')
        return False

    def poll(self, *, default=None):
        if not self._silent:
            raise ProhibitedOperationError('poll')
        return default

    async def take(self, *, default=None, timeout=None):
        if not self._silent:
            raise ProhibitedOperationError('take')
        return default


shield_from_read = ReadShield


class WriteShield(ChannelDecoratorBase):
    """Shield a channel from having items written.

    If silent is false then calling .capacit(), .offer(), or
    .put() will raise a ProhibitedOperationError.
    """

    def __init__(self, channel, *, silent=False,
                 _delegate_methods=_delegate_methods):
        super().__init__(channel, silent=silent)
        _delegate_methods(receiver=self, target=channel)

    async def capacity(self, *, timeout=None):
        if not self._silent:
            raise ProhibitedOperationError('capacity')
        return False

    def offer(self, x, *, default=None):
        if not self._silent:
            raise ProhibitedOperationError('offer')
        return False

    async def put(self, x, default=None, timeout=None):
        if not self._silent:
            raise ProhibitedOperationError('put')
        return False


shield_from_write = WriteShield
