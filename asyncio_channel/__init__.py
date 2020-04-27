"""Asynchronous channels and utilities."""

__all__ = ('ProhibitedOperationError', 'complete_one',
           'create_blocking_buffer', 'create_dropping_buffer',
           'create_sliding_buffer', 'create_channel', 'create_mix',
           'create_multiple', 'create_publication', 'itermerge',
           'iterzip', 'merge', 'map', 'onto_channel', 'to_channel',
           'pipe', 'reduce', 'shield_from_close', 'shield_from_read',
           'shield_from_write', 'split')

__version__ = '0.9'

from ._complete_one import complete_one
from ._buffer import (create_blocking_buffer, create_dropping_buffer,
                      create_sliding_buffer)
from ._create_channel import create_channel
from ._create_mix import create_mix
from ._create_multiple import create_multiple
from ._create_publication import create_publication
from ._iter import itermerge, iterzip
from ._merge import merge
from ._map import map
from ._onto_channel import onto_channel, to_channel
from ._pipe import pipe
from ._reduce import reduce
from ._shield import (ProhibitedOperationError, shield_from_close,
                      shield_from_read, shield_from_write)
from ._split import split
