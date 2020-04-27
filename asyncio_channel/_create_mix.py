__all__ = ('create_mix',)

from asyncio import Event, create_task
from itertools import chain

from ._channel import Channel
from ._mixin import ReprMixin
from ._util import wait_all, wait_first


def _range_from(start, end, at, *, _chain=chain):
    """Produce a sequence [start, end), beginning at "at".

    If "at" is greater than "start" and sequence reaches "end",
    it will wrap to "start".

    Example:
    >>> list(_range_from(start=0, end=10, at=7))
    [7, 8, 9, 0, 1, 2, 3, 4, 5, 6]
    """
    return _chain(range(at, end), range(start, at))


async def _mix(out, mix, restart, notify, *,
               _range_from=_range_from, _wait_all=wait_all,
               _wait_first=wait_first):
    """Transer items from mix channels to out channel."""
    at = 0
    while True:
        # Ensure restart isn't still set.
        restart.clear()

        # Wait for one of the following conditions:
        await _wait_first(
            # 1. restart flag is set.
            restart.wait(),
            # 2. out channel is closed.
            out.closed(),
            # 3. out channel has capacity and at least one mix channel
            #    has an item.
            _wait_all(
                out.capacity(),
                _wait_first(*(ch.item() for ch in mix))))

        if out.is_closed():
            break  # End transfer task.
        if restart.is_set():
            # One or more mix channels should no longer be included,
            # abandon the current attempt and restart to pick up changes.
            at = 0
            continue

        # Attempt to read from the mix channels with equal frequency by
        # checking the channel after the channel that was read during
        # the last attempt.
        nmix = len(mix)
        at = min(at, nmix - 1)
        for i in _range_from(0, nmix, at):
            ch = mix[i]
            if not ch.empty():  # Sanity check.
                x = ch.poll()
                out.offer(x)
                break

    notify()  # that transfer task has ended.


async def _drain(out, mute, restart, *,
                 _range_from=_range_from, _wait_all=wait_all,
                 _wait_first=wait_first):
    """Drain items from mute channels."""
    at = 0
    while True:
        # Ensure restart isn't still set.
        restart.clear()

        # Wait for one of the following conditions:
        await _wait_first(
            # 1. restart flag is set.
            restart.wait(),
            # 2. out channel is closed.
            out.closed(),
            # 3. At least one mute channel has an item.
            _wait_first(*(ch.item() for ch in mute)))

        if out.is_closed():
            break  # End drain task.
        if restart.is_set():
            # One or more mute channels should no longer be included,
            # abandon the current attempt and restart to pick up changes.
            at = 0
            continue

        # Attempt to read from the mix channels with equal frequency by
        # checking the channel after the channel that was read during
        # the last attempt.
        nmute = len(mute)
        at = min(at, nmute - 1)
        for i in _range_from(0, nmute, at):
            ch = mute[i]
            if not ch.empty():  # Sanity check.
                ch.poll()
                break


class ChannelMix(ReprMixin):
    """Create a mix of input channels onto output channel.

    Each input channel may have the following flags set:
    - priority - when mix is in priority mode, items will be taken and put
        on output channel.
    - mute - items will be taken but not put on output channel.
    - pause - items will not be taken.

    The mix may be put in one of two priority modes:
    - priority-mute - input channels flagged as priority will have items
        taken and put on output channel, regardless of their mute or pause
        flag statuses; any other non-paused input channels will be muted.
    - priority-pause - Same as priority-mute except that all non-priority
        input channels will be paused.
    """

    PRIORITY_OFF = 0
    PRIORITY_MUTE = 1
    PRIORITY_PAUSE = 2

    _ALLOWED_MODES = (PRIORITY_OFF, PRIORITY_MUTE, PRIORITY_PAUSE)

    def __init__(self, out, *,
                 _create_task=create_task, _Event=Event, _mix=_mix,
                 _drain=_drain):
        self._srcs = {}
        self._priority_mode = False
        self._done = False
        self._mix = mix = []
        self._mute = mute = []
        self._restart_mix = restart_mix = _Event()
        self._restart_mute = restart_mute = _Event()
        _create_task(_mix(out, mix, restart_mix, self._notify))
        _create_task(_drain(out, mute, restart_mute))

    @property
    def priority_mode(self):
        return self._priority_mode

    @priority_mode.setter
    def priority_mode(self, mode, *,
                      _allowed_modes=_ALLOWED_MODES):
        if mode not in _allowed_modes:
            raise ValueError('invalid priority mode')

        if self._priority_mode != mode:
            self._priority_mode = mode
            self._update()

        return mode

    def add_input(self, ch):
        """Add input channel to mix.

        Associated flags are all set to False.
        """
        if self._done:
            return

        self._srcs[id(ch)] = {'chan': ch}
        if not self._priority_mode:
            self._mix.append(ch)
            self._restart()

    def remove_input(self, ch):
        """Remove input channel from mix."""
        if self._done:
            return

        try:
            del self._srcs[id(ch)]
        except KeyError:
            pass

        try:
            self._mix.remove(ch)
        except ValueError:
            pass
        else:
            self._restart()
            return

        try:
            self._mute.remove(ch)
        except ValueError:
            pass
        else:
            self._restart()

    def remove_all_inputs(self):
        """Remove all input channels from the mix."""
        if not self._done:
            self._srcs.clear()
            self._mix.clear()
            self._mute.clear()
            self._restart()

    def toggle(self, *ch_opts):
        """Associate control flags with input channels.

        Control flags are specified as a dict with boolean entries for
        priority, mute, or pause and are merged with the currently
        associated flags.

        This method may be used to add new channels to the mix.
        """
        if not ch_opts:
            raise ValueError('no arguments')
        if len(ch_opts) % 2 != 0:
            raise ValueError('odd number of arguments')

        new_srcs = {}
        get_src = self._srcs.get
        allowed_keys = {'priority', 'mute', 'pause'}
        for i in range(0, len(ch_opts), 2):
            j = i + 1
            ch = ch_opts[i]
            opts = ch_opts[j]

            if not isinstance(ch, Channel):
                raise TypeError(
                    f'argument {i} must be a channel, '
                    f'not a {type(ch).__name__}')
            if not isinstance(opts, dict):
                raise TypeError(
                    f'argument {j} must be a dict, '
                    f'not a {type(opts).__name__}')

            disallowed_keys = frozenset(opts.keys()).difference(allowed_keys)
            if disallowed_keys:
                raise KeyError(
                    f'argument {j} contains keys '
                    f'{", ".join(sorted(disallowed_keys))}, '
                    f'only {", ".join(sorted(allowed_keys))} are allowed')

            ch_id = id(ch)
            src = get_src(ch_id)
            if not src:
                src = dict(chan=ch, **opts)
            else:
                src.update(opts)
            new_srcs[ch_id] = src

        if not self._done:
            self._srcs = new_srcs
            self._update()

    def _update(self):
        """Update the mix and mute channel lists."""
        if self._done:
            return

        priority_mode = self._priority_mode
        if priority_mode == self.PRIORITY_MUTE:
            self._sort_priority_mute()
        elif priority_mode == self.PRIORITY_PAUSE:
            self._sort_priority_pause()
        else:
            self._sort_mix()
        self._restart()

    def _sort_mix(self):
        """Sort channels for regular mix mode."""
        mix = self._mix
        mute = self._mute
        add_mix = mix.append
        add_mute = mute.append
        mix.clear()
        mute.clear()

        for src in self._srcs.values():
            get_src_flag = src.get

            if not get_src_flag('pause'):
                add = add_mute if get_src_flag('mute') else add_mix
                add(src['chan'])

    def _sort_priority_mute(self):
        """Sort channels for priority-mute mode."""
        mix = self._mix
        mute = self._mute
        add_mix = mix.append
        add_mute = mute.append
        mix.clear()
        mute.clear()

        for src in self._srcs.values():
            get_src_flag = src.get

            if get_src_flag('priority'):
                add_mix(src['chan'])
            elif not get_src_flag('pause'):
                add_mute(src['chan'])

    def _sort_priority_pause(self):
        """Sort channels for priority-pause mode."""
        mix = self._mix
        add_mix = mix.append
        mix.clear()
        self._mute.clear()

        for src in self._srcs.values():
            if src.get('priority'):
                add_mix(src['chan'])

    def _restart(self):
        """Signal tasks to restart."""
        self._restart_mix.set()
        self._restart_mute.set()

    def _notify(self):
        """Clean up the mix."""
        self.remove_all_inputs()
        self._done = True

    def _format(self):
        return 'done' if self._done else 'active'


create_mix = ChannelMix
