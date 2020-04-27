__all__ = ('complete_one',)

from asyncio import create_task

from ._channel import Channel
from ._util import wait_first


def _exec_first_ready(ch_ops, channel=Channel):
    """Execute the first ch_op which is ready."""
    for ch_op in ch_ops:
        if isinstance(ch_op, channel):
            ch = ch_op
            if not ch.empty():
                x = ch.poll()
                return x, ch
        else:
            ch, x = ch_op
            status = ch.offer(x)
            if status:
                return True, ch


def _get_tasks_waiting_for_ready(
        ch_ops,
        channel=Channel,
        create_task=create_task):
    """Get tasks which wait for each ch_op to be ready."""
    tasks = []
    for ch_op in ch_ops:
        if isinstance(ch_op, Channel):
            tasks.append(create_task(ch_op.item()))
        else:
            ch, _ = ch_op
            tasks.append(create_task(ch.capacity()))
    return tasks


def _exec_first_ready_in_order(
        ready_tasks,
        ordered_tasks,
        ch_ops,
        _exec_first_ready=_exec_first_ready):
    """Execute the first ready task from ordered_task.

    Returns a tuple of (execution_output, retry_ch_opts), one element will be
    None.
    """
    next_ch_opts = []
    for i, task in enumerate(ordered_tasks):
        if task in ready_tasks:
            ready = ch_ops[i]
            out = _exec_first_ready((ready,))
            if out:
                return out, None
        else:
            next_ch_opts.append(ch_ops[i])
    return None, next_ch_opts


def _exec_first_available_ready(
        ready_tasks,
        all_tasks,
        ch_ops,
        _exec_first_ready=_exec_first_ready):
    """Execute the first ready task.

    Returns a tuple of (execution_output, retry_ch_opts), one element will be
    None.
    """
    duds = []
    for task in ready_tasks:
        index = all_tasks.index(task)
        ready = ch_ops[index]
        out = _exec_first_ready((ready,))
        if out:
            return out, None
        duds.append(ch_ops[index])
    return None, list(frozenset(ch_ops).difference(duds))


async def complete_one(
        *ch_ops, priority=False,
        _exec_first_ready=_exec_first_ready,
        _exec_first_ready_in_order=_exec_first_ready_in_order,
        _exec_first_available_ready=_exec_first_available_ready,
        _get_tasks_waiting_for_ready=_get_tasks_waiting_for_ready,
        _wait_first=wait_first,
        **kwargs):
    """Complete at most one channel operation.

    A "ch_op" is either a channel, which will be read from, or a tuple of
    (channel, x), which will add x to channel.

    Returns a tuple (value, channel).  "value" will be True is ch_op was an add
    operation, or the value read if it was a read operation.

    If keyword argument "default" is present and no ch_op is immediately ready
    then returns a tuple (default, 'default').

    If keyword argument "priority" is True then the first ch_op ready from the
    ordered list of arguments will be run.  Otherwise, if more than one ch_op
    is ready the selection will be non-deterministic.
    """
    out = _exec_first_ready(ch_ops)
    if out:
        return out
    elif 'default' in kwargs:
        return kwargs['default'], 'default'

    ch_ops = list(ch_ops)
    while ch_ops:
        # Get this round's list of ready operations.
        tasks = _get_tasks_waiting_for_ready(ch_ops)
        done, _ = await _wait_first(*tasks)

        exec_ = _exec_first_available_ready
        if priority and len(done) > 1:
            exec_ = _exec_first_ready_in_order

        out, ch_ops = exec_(done, tasks, ch_ops)
        if out:
            return out

    return None, None
