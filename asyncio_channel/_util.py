__all__ = ('wait_all', 'wait_first')

from asyncio import FIRST_COMPLETED, CancelledError, Task, create_task, wait


async def wait_all(
        *coros_or_tasks,
        timeout=None,
        create_task=create_task,
        wait=wait,
        CancelledError=CancelledError,
        Task=Task):
    """Wait for all tasks to complete.

    Returns two tuples: completed tasks, pending tasks.  If timeout is
    provided then completed tasks set may be empty.
    """
    tasks = tuple(
        ct if isinstance(ct, Task) else create_task(ct)
        for ct in coros_or_tasks)

    try:
        done, pending = await wait(tasks, timeout=timeout)
    except CancelledError:
        for task in tasks:
            if not task.done():
                task.cancel()

        raise
    else:
        for task in pending:
            task.cancel()

        return done, pending


async def wait_first(
        *coros_or_tasks,
        timeout=None,
        wait=wait,
        return_when=FIRST_COMPLETED,
        CancelledError=CancelledError):
    """Wait for first task to complete.

    Returns two tuples: completed tasks, pending tasks.  If timeout is
    provided then completed tasks set may be empty.
    """
    tasks = tuple(
        ct if isinstance(ct, Task) else create_task(ct)
        for ct in coros_or_tasks)

    try:
        done, pending = await wait(
            tasks,
            timeout=timeout,
            return_when=return_when)
    except CancelledError:
        for task in tasks:
            if not task.done():
                task.cancel()

        raise
    else:
        for task in pending:
            task.cancel()

        return done, pending
