from __future__ import annotations

__all__ = ('complete_one',)

from asyncio import Task, create_task
from collections.abc import Callable
from typing import Any

from ._types import AnyChannel, ReadableChannel, WritableChannel, _WaitFn
from ._util import wait_first

# A ch_op is either a channel to read from, or a (channel, value) pair to
# write to.
_ChOp = ReadableChannel | tuple[WritableChannel, Any]
_ExecFn = Callable[..., tuple[Any, AnyChannel] | None]


def _exec_first_ready(
        ch_ops: tuple[_ChOp, ...] | list[_ChOp],
) -> tuple[Any, AnyChannel] | None:
    """Execute the first ch_op which is ready."""
    # A take-op is any readable channel; a put-op is a (channel, x) tuple.
    for ch_op in ch_ops:
        if not isinstance(ch_op, tuple):
            ch = ch_op
            if not ch.empty():
                x = ch.poll()
                return x, ch
        else:
            ch, x = ch_op
            status = ch.offer(x)
            if status:
                return True, ch
    return None


def _get_tasks_waiting_for_ready(
        ch_ops: list[_ChOp],
        create_task: Callable[..., Task[Any]] = create_task,
) -> list[Task[Any]]:
    """Get tasks which wait for each ch_op to be ready."""
    tasks = []
    for ch_op in ch_ops:
        if not isinstance(ch_op, tuple):
            tasks.append(create_task(ch_op.item()))
        else:
            ch, _ = ch_op
            tasks.append(create_task(ch.capacity()))
    return tasks


def _exec_first_ready_in_order(
        ready_tasks: set[Task[Any]],
        ordered_tasks: list[Task[Any]],
        ch_ops: list[_ChOp],
        _exec_first_ready: _ExecFn = _exec_first_ready,
) -> tuple[tuple[Any, AnyChannel] | None, list[_ChOp] | None]:
    """Execute the first ready task from ordered_task.

    Returns a tuple of (execution_output, retry_ch_opts), one element will be
    None.
    """
    next_ch_opts: list[_ChOp] = []
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
        ready_tasks: set[Task[Any]],
        all_tasks: list[Task[Any]],
        ch_ops: list[_ChOp],
        _exec_first_ready: _ExecFn = _exec_first_ready,
) -> tuple[tuple[Any, AnyChannel] | None, list[_ChOp] | None]:
    """Execute the first ready task.

    Returns a tuple of (execution_output, retry_ch_opts), one element will be
    None.
    """
    dud_ids: set[int] = set()
    for task in ready_tasks:
        index = all_tasks.index(task)
        ready = ch_ops[index]
        out = _exec_first_ready((ready,))
        if out:
            return out, None
        dud_ids.add(index)
    # Preserve argument order (required for priority semantics) and
    # avoid hashing ch_ops (put-op values may be unhashable).
    return None, [op for i, op in enumerate(ch_ops) if i not in dud_ids]


async def complete_one(
        *ch_ops: _ChOp, priority: bool = False,
        _exec_first_ready: _ExecFn = _exec_first_ready,
        _exec_first_ready_in_order: Callable[..., Any] = _exec_first_ready_in_order,
        _exec_first_available_ready: Callable[..., Any] = _exec_first_available_ready,
        _get_tasks_waiting_for_ready: Callable[..., list[Task[Any]]] = (
            _get_tasks_waiting_for_ready),
        _wait_first: _WaitFn = wait_first,
        **kwargs: Any) -> tuple[Any, AnyChannel | str | None]:
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

    ch_ops_list = list(ch_ops)
    while ch_ops_list:
        # Get this round's list of ready operations.
        tasks = _get_tasks_waiting_for_ready(ch_ops_list)
        done, _ = await _wait_first(*tasks)

        exec_ = _exec_first_available_ready
        if priority and len(done) > 1:
            exec_ = _exec_first_ready_in_order

        out, ch_ops_list = exec_(done, tasks, ch_ops_list)
        if out:
            return out

    return None, None
