from __future__ import annotations

__all__ = ('ReprMixin',)


class ReprMixin:
    """Provides a repr() method.

    Uses a supplied _format() method to populate description.
    """

    def __repr__(self) -> str:
        return f'<{type(self).__name__} {self._format()} at {id(self):#x}>'
