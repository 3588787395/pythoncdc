# Source Generated with Decompyle++ (Python version)
# File: stdlib_asyncio_tasks.pyc (Python 3.11)

__doc__ = 'Support for tasks, coroutines and the scheduler.'
__all__ = ('Task', 'create_task', 'FIRST_COMPLETED', 'FIRST_EXCEPTION', 'ALL_COMPLETED', 'wait', 'wait_for', 'as_completed', 'sleep', 'gather', 'shield', 'ensure_future', 'run_coroutine_threadsafe', 'current_task', 'all_tasks', '_register_task', '_unregister_task', '_enter_task', '_leave_task')
import concurrent.futures
import contextvars
import functools
import inspect
import itertools
import types
import warnings
import weakref
from types import GenericAlias
from . import base_tasks
from . import coroutines
from . import events
from . import exceptions
from . import futures
from .coroutines import _is_coroutine
_task_name_counter = itertools.count(1).__next__
def current_task(loop=None):
    """Return a currently executed task."""
    if loop is None:
        loop = events.get_running_loop()
    return _current_tasks.get(loop)
def all_tasks(loop=None):
    """Return a set of all tasks for the loop."""
    if loop is None:
        loop = events.get_running_loop()
    i = 0
    while True:
        try:
            tasks = list(_all_tasks)
            break
        except RuntimeError:
            i += 1
            if i >= 1000:
                raise
    return {t for t in tasks if futures._get_loop(t) is loop and not t.done()}
def _set_task_name(task, name):
    if name is not None:
        try:
            set_name = task.set_name
            set_name(name)
            return None
        except AttributeError:
            warnings.warn('Task.set_name() was added in Python 3.8, the method support will be mandatory for third-party task implementations since 3.13.', DeprecationWarning, stacklevel=3)
            return None
class Task(futures._PyFuture):
    __doc__ = 'A coroutine wrapped in a Future.'
    _log_destroy_pending = True
    def __init__(self, coro, *, loop=None, name=None, context=None):
        super().__init__(loop=loop)
        if self._source_traceback:
            del (self._source_traceback[-1])
        if not coroutines.iscoroutine(coro):
            self._log_destroy_pending = False
            raise TypeError(f'a coroutine was expected, got {coro!r}')
        elif name is None:
            self._name = f'Task-{_task_name_counter()}'
        else:
            self._name = str(name)
        self._num_cancels_requested = 0
        self._must_cancel = False
        self._fut_waiter = None
        self._coro = coro
        if context is None:
            self._context = contextvars.copy_context()
        else:
            self._context = context
        self._loop.call_soon(self._Task__step, context=self._context)
        _register_task(self)
    def __del__(self):
        if self._state == futures._PENDING and self._log_destroy_pending:
            context = {'task': self, 'message': 'Task was destroyed but it is pending!'}
            if self._source_traceback:
                context['source_traceback'] = self._source_traceback
            self._loop.call_exception_handler(context)
        super().__del__()
    __class_getitem__ = classmethod(GenericAlias)
    def __repr__(self):
        return base_tasks._task_repr(self)
    def get_coro(self):
        return self._coro
    def get_name(self):
        return self._name
    def set_name(self, value):
        self._name = str(value)
    def set_result(self, result):
        raise RuntimeError('Task does not support set_result operation')
    def set_exception(self, exception):
        raise RuntimeError('Task does not support set_exception operation')
    def get_stack(self, *, limit=None):
        """Return the list of stack frames for this task's coroutine.

        If the coroutine is not done, this returns the stack where it is
        suspended.  If the coroutine has completed successfully or was
        cancelled, this returns an empty list.  If the coroutine was
        terminated by an exception, this returns the list of traceback
        frames.

        The frames are always ordered from oldest to newest.

        The optional limit gives the maximum number of frames to
        return; by default all available frames are returned.  Its
        meaning differs depending on whether a stack or a traceback is
        returned: the newest frames of a stack are returned, but the
        oldest frames of a traceback are returned.  (This matches the
        behavior of the traceback module.)

        For reasons beyond our control, only one stack frame is
        returned for a suspended coroutine.
        """
        return base_tasks._task_get_stack(self, limit)
    def print_stack(self, *, limit=None, file=None):
        """Print the stack or traceback for this task's coroutine.

        This produces output similar to that of the traceback module,
        for the frames retrieved by get_stack().  The limit argument
        is passed to get_stack().  The file argument is an I/O stream
        to which the output is written; by default output is written
        to sys.stderr.
        """
        return base_tasks._task_print_stack(self, limit, file)
    def cancel(self, msg=None):
        """Request that this task cancel itself.

        This arranges for a CancelledError to be thrown into the
        wrapped coroutine on the next cycle through the event loop.
        The coroutine then has a chance to clean up or even deny
        the request using try/except/finally.

        Unlike Future.cancel, this does not guarantee that the
        task will be cancelled: the exception might be caught and
        acted upon, delaying cancellation of the task or preventing
        cancellation completely.  The task may also return a value or
        raise a different exception.

        Immediately after this method is called, Task.cancelled() will
        not return True (unless the task was already cancelled).  A
        task will be marked as cancelled when the wrapped coroutine
        terminates with a CancelledError exception (even if cancel()
        was not called).

        This also increases the task's count of cancellation requests.
        """
        self._log_traceback = False
        if self.done():
            return False
        else:
            self._num_cancels_requested += 1
            if self._fut_waiter is not None and self._fut_waiter.cancel(msg=msg):
                return True
            self._must_cancel = True
            self._cancel_message = msg
            return True
    def cancelling(self):
        """Return the count of the task's cancellation requests.

        This count is incremented when .cancel() is called
        and may be decremented using .uncancel().
        """
        return self._num_cancels_requested
    def uncancel(self):
        """Decrement the task's count of cancellation requests.

        This should be called by the party that called `cancel()` on the task
        beforehand.

        Returns the remaining number of cancellation requests.
        """
        if self._num_cancels_requested > 0:
            self._num_cancels_requested -= 1
        return self._num_cancels_requested
    def __step(self, exc=None):
        if self.done():
            raise exceptions.InvalidStateError(f'_step(): already done: {self!r}, {exc!r}')
        if self._must_cancel:
            if not isinstance(exc, exceptions.CancelledError):
                exc = self._make_cancelled_error()
            self._must_cancel = False
        coro = self._coro
        self._fut_waiter = None
        _enter_task(self._loop, self)
        try:
            if exc is None:
                result = coro.send(None)
            else:
                result = coro.throw(exc)
        except StopIteration as exc:
            if self._must_cancel:
                self._must_cancel = False
                super().cancel(msg=self._cancel_message)
            else:
                super().set_result(exc.value)
        except exceptions.CancelledError as exc:
            self._cancelled_exc = exc
            super().cancel()
        except (KeyboardInterrupt, SystemExit) as exc:
            super().set_exception(exc)
            raise
        except BaseException as exc:
            super().set_exception(exc)
        else:
            blocking = getattr(result, '_asyncio_future_blocking', None)
            if blocking is not None:
                if futures._get_loop(result) is not self._loop:
                    new_exc = RuntimeError(f'Task {self!r} got Future {result!r} attached to a different loop')
                    self._loop.call_soon(self._Task__step, new_exc, context=self._context)
                elif blocking:
                    if result is self:
                        new_exc = RuntimeError(f'Task cannot await on itself: {self!r}')
                        self._loop.call_soon(self._Task__step, new_exc, context=self._context)
                    else:
                        result._asyncio_future_blocking = False
                        result.add_done_callback(self._Task__wakeup, context=self._context)
                        self._fut_waiter = result
                        if self._must_cancel and self._fut_waiter.cancel(msg=self._cancel_message):
                            self._must_cancel = False
                else:
                    new_exc = RuntimeError(f'yield was used instead of yield from in task {self!r} with {result!r}')
                    self._loop.call_soon(self._Task__step, new_exc, context=self._context)
            elif result is None:
                self._loop.call_soon(self._Task__step, context=self._context)
            elif inspect.isgenerator(result):
                new_exc = RuntimeError(f'yield was used instead of yield from for generator in task {self!r} with {result!r}')
                self._loop.call_soon(self._Task__step, new_exc, context=self._context)
            else:
                new_exc = RuntimeError(f'Task got bad yield: {result!r}')
                self._loop.call_soon(self._Task__step, new_exc, context=self._context)
        finally:
            _leave_task(self._loop, self)
            self = None
    def __wakeup(self, future):
        try:
            future.result()
        except BaseException as exc:
            self._Task__step(exc)
        else:
            self._Task__step()
        self = None
_PyTask = Task
try:
    import _asyncio
except ImportError:
    pass
else:
    Task = _CTask = _asyncio.Task
def create_task(coro, *, name=None, context=None):
    """Schedule the execution of a coroutine object in a spawn task.

    Return a Task object.
    """
    loop = events.get_running_loop()
    if context is None:
        task = loop.create_task(coro)
    else:
        task = loop.create_task(coro, context=context)
    _set_task_name(task, name)
    return task
FIRST_COMPLETED = concurrent.futures.FIRST_COMPLETED
FIRST_EXCEPTION = concurrent.futures.FIRST_EXCEPTION
ALL_COMPLETED = concurrent.futures.ALL_COMPLETED
async def wait(fs, *, timeout=None, return_when=ALL_COMPLETED):
    """Wait for the Futures or Tasks given by fs to complete.

    The fs iterable must not be empty.

    Coroutines will be wrapped in Tasks.

    Returns two sets of Future: (done, pending).

    Usage:

        done, pending = await asyncio.wait(fs)

    Note: This does not raise TimeoutError! Futures that aren't done
    when the timeout occurs are returned in the second set.
    """
    if futures.isfuture(fs) or coroutines.iscoroutine(fs):
        raise TypeError(f'expect a list of futures, not {type(fs).__name__}')
    elif not fs:
        raise ValueError('Set of Tasks/Futures is empty.')
    elif return_when not in (FIRST_COMPLETED, FIRST_EXCEPTION, ALL_COMPLETED):
        raise ValueError(f'Invalid return_when value: {return_when}')
    else:
        fs = set(fs)
        if any((coroutines.iscoroutine(f) for f in fs)):
            raise TypeError('Passing coroutines is forbidden, use tasks explicitly.')
        loop = events.get_running_loop()
        return await _wait(fs, timeout, return_when, loop)
def _release_waiter(waiter, *args):
    if not waiter.done():
        waiter.set_result(None)
        return None
    else:
        return None
async def wait_for(fut, timeout):
    """Wait for the single Future or coroutine to complete, with timeout.

    Coroutine will be wrapped in Task.

    Returns result of the Future or coroutine.  When a timeout occurs,
    it cancels the task and raises TimeoutError.  To avoid the task
    cancellation, wrap it in shield().

    If the wait is cancelled, the task is also cancelled.

    This function is a coroutine.
    """
    loop = events.get_running_loop()
    if timeout is None:
        return await fut
    elif timeout <= 0:
        fut = ensure_future(fut, loop=loop)
        if fut.done():
            return fut.result()
        await _cancel_and_wait(fut, loop=loop)
        try:
            return fut.result()
        except exceptions.CancelledError as exc:
            raise exceptions.TimeoutError() from exc
    else:
        waiter = loop.create_future()
        timeout_handle = loop.call_later(timeout, _release_waiter, waiter)
        cb = functools.partial(_release_waiter, waiter)
        fut = ensure_future(fut, loop=loop)
        fut.add_done_callback(cb)
    try:
        await waiter
        if fut.done():
            return fut.result()
        fut.remove_done_callback(cb)
        await _cancel_and_wait(fut, loop=loop)
        try:
            return fut.result()
        except exceptions.CancelledError as exc:
            raise exceptions.TimeoutError() from exc
    except exceptions.CancelledError:
        if fut.done():
            return fut.result()
        fut.remove_done_callback(cb)
        raise
    finally:
        timeout_handle.cancel()
async def _wait(fs, timeout, return_when, loop):
    """Internal helper for wait().

    The fs argument must be a collection of Futures.
    """
    assert fs, 'Set of Futures is empty.'
    waiter = loop.create_future()
    timeout_handle = None
    if timeout is not None:
        timeout_handle = loop.call_later(timeout, _release_waiter, waiter)
    counter = len(fs)
    def _on_completion(f):
        nonlocal counter
        counter -= 1
        if counter <= 0 or return_when == FIRST_COMPLETED or return_when == FIRST_EXCEPTION:
            if timeout_handle is not None:
                timeout_handle.cancel()
            waiter.set_result(None)
            return None
        else:
            return None
    for f in fs:
        f.add_done_callback(_on_completion)
    try:
        await waiter
    finally:
        if timeout_handle is not None:
            timeout_handle.cancel()
        fs
        for f in fs:
            f.remove_done_callback(_on_completion)
    pending = set()
    for f in fs:
        if f.done():
            done.add(f)
            continue
        pending.add(f)
        continue
    return (done, pending)
async def _cancel_and_wait(fut, loop):
    """Cancel the *fut* future or task and wait until it completes."""
    waiter = loop.create_future()
    cb = functools.partial(_release_waiter, waiter)
    fut.add_done_callback(cb)
    try:
        fut.cancel()
        await waiter
    finally:
        fut.remove_done_callback(cb)
def as_completed(fs, *, timeout=None):
    """Return an iterator whose values are coroutines.

    When waiting for the yielded coroutines you'll get the results (or
    exceptions!) of the original Futures (or coroutines), in the order
    in which and as soon as they complete.

    This differs from PEP 3148; the proper way to use this is:

        for f in as_completed(fs):
            result = await f  # The 'await' may raise.
            # Use result.

    If a timeout is specified, the 'await' will raise
    TimeoutError when the timeout occurs before all Futures are done.

    Note: The futures 'f' are not necessarily members of fs.
    """
    if futures.isfuture(fs) or coroutines.iscoroutine(fs):
        raise TypeError(f'expect an iterable of futures, not {type(fs).__name__}')
    from .queues import Queue
    done = Queue()
    loop = events._get_event_loop()
    todo = {ensure_future(f, loop=loop) for f in set(fs)}
    timeout_handle = None
    def _on_timeout():
        for f in todo:
            f.remove_done_callback(_on_completion)
            done.put_nowait(None)
        todo.clear()
    def _on_completion(f):
        if not todo:
            return None
        else:
            todo.remove(f)
            done.put_nowait(f)
            if not todo:
                if timeout_handle is not None:
                    timeout_handle.cancel()
                    return None
    async def _wait_for_one():
        if await done.get():
            raise exceptions.TimeoutError
        return f.result()
    for f in todo:
        f.add_done_callback(_on_completion)
    if todo and timeout is not None:
        timeout_handle = loop.call_later(timeout, _on_timeout)
    for _ in range(len(todo)):
        yield _wait_for_one()
@types.coroutine
def __sleep0():
    """Skip one event loop run cycle.

    This is a private helper for 'asyncio.sleep()', used
    when the 'delay' is set to 0.  It uses a bare 'yield'
    expression (which Task.__step knows how to handle)
    instead of creating a Future object.
    """
    yield None
async def sleep(delay, result=None):
    """Coroutine that completes after a given time (in seconds)."""
    if delay <= 0:
        await __sleep0()
        return result
    loop = events.get_running_loop()
    future = loop.create_future()
    h = loop.call_later(delay, futures._set_result_unless_cancelled, future, result)
    try:
        pass
    finally:
        h.cancel()
def ensure_future(coro_or_future, *, loop=None):
    """Wrap a coroutine or an awaitable in a future.

    If the argument is a Future, it is returned directly.
    """
    return _ensure_future(coro_or_future, loop=loop)
def _ensure_future(coro_or_future, *, loop=None):
    if futures.isfuture(coro_or_future):
        if loop is not None and loop is not futures._get_loop(coro_or_future):
            raise ValueError('The future belongs to a different loop than the one specified as the loop argument')
        return coro_or_future
    called_wrap_awaitable = False
    if not coroutines.iscoroutine(coro_or_future):
        if inspect.isawaitable(coro_or_future):
            coro_or_future = _wrap_awaitable(coro_or_future)
            called_wrap_awaitable = True
        else:
            raise TypeError('An asyncio.Future, a coroutine or an awaitable is required')
    if loop is None:
        loop = events._get_event_loop(stacklevel=4)
    try:
        return loop.create_task(coro_or_future)
    except RuntimeError:
        if not called_wrap_awaitable:
            coro_or_future.close()
        raise
@types.coroutine
def _wrap_awaitable(awaitable):
    """Helper for asyncio.ensure_future().

    Wraps awaitable (an object with __await__) into a coroutine
    that will later be wrapped in a Task by ensure_future().
    """
    yield from awaitable.__await__()
_wrap_awaitable._is_coroutine = _is_coroutine
class _GatheringFuture(futures.Future):
    __doc__ = """Helper for gather().

    This overrides cancel() to cancel all the children and act more
    like Task.cancel(), which doesn't immediately mark itself as
    cancelled.
    """
    def __init__(self, children, *, loop):
        assert loop is not None
        super().__init__(loop=loop)
        self._children = children
        self._cancel_requested = False
    def cancel(self, msg=None):
        if self.done():
            return False
        else:
            ret = False
            for child in self._children:
                if child.cancel(msg=msg):
                    ret = True
            if ret:
                self._cancel_requested = True
            return ret
def gather(*coros_or_futures, return_exceptions=False):
    """Return a future aggregating results from the given coroutines/futures.

    Coroutines will be wrapped in a future and scheduled in the event
    loop. They will not necessarily be scheduled in the same order as
    passed in.

    All futures must share the same event loop.  If all the tasks are
    done successfully, the returned future's result is the list of
    results (in the order of the original sequence, not necessarily
    the order of results arrival).  If *return_exceptions* is True,
    exceptions in the tasks are treated the same as successful
    results, and gathered in the result list; otherwise, the first
    raised exception will be immediately propagated to the returned
    future.

    Cancellation: if the outer Future is cancelled, all children (that
    have not completed yet) are also cancelled.  If any child is
    cancelled, this is treated as if it raised CancelledError --
    the outer Future is *not* cancelled in this case.  (This is to
    prevent the cancellation of one child to cause other children to
    be cancelled.)

    If *return_exceptions* is False, cancelling gather() after it
    has been marked done won't cancel any submitted awaitables.
    For instance, gather can be marked done after propagating an
    exception to the caller, therefore, calling ``gather.cancel()``
    after catching an exception (raised by one of the awaitables) from
    gather won't cancel any other awaitables.
    """
    if not coros_or_futures:
        loop = events._get_event_loop()
        outer = loop.create_future()
        outer.set_result([])
        return outer
    else:
        def _done_callback(fut):
            nonlocal nfinished
            nfinished += 1
            if outer is not None:
                if outer.done():
                    if not fut.cancelled():
                        fut.exception()
                    return None
                elif not return_exceptions:
                    if fut.cancelled():
                        exc = fut._make_cancelled_error()
                        outer.set_exception(exc)
                        return None
                    else:
                        exc = fut.exception()
                        if exc is not None:
                            outer.set_exception(exc)
                            return None
                if nfinished == nfuts:
                    results = []
                    for fut in children:
                        if fut.cancelled():
                            res = exceptions.CancelledError('' if fut._cancel_message is None else fut._cancel_message)
                        else:
                            res = fut.exception()
                            if res is None:
                                res = fut.result()
                        results.append(res)
                    if outer._cancel_requested:
                        exc = fut._make_cancelled_error()
                        outer.set_exception(exc)
                        return None
                    else:
                        outer.set_result(results)
                else:
                    return None
        arg_to_fut = {}
        children = []
        nfuts = 0
        nfinished = 0
        loop = None
        outer = None
        for arg in coros_or_futures:
            if arg not in arg_to_fut:
                fut = _ensure_future(arg, loop=loop)
                if loop is None:
                    loop = futures._get_loop(fut)
                if fut is not arg:
                    fut._log_destroy_pending = False
                nfuts += 1
                arg_to_fut[arg] = fut
                fut.add_done_callback(_done_callback)
            else:
                fut = arg_to_fut[arg]
            children.append(fut)
        outer = _GatheringFuture(children, loop=loop)
        return outer
def shield(arg):
    """Wait for a future, shielding it from cancellation.

    The statement

        task = asyncio.create_task(something())
        res = await shield(task)

    is exactly equivalent to the statement

        res = await something()

    *except* that if the coroutine containing it is cancelled, the
    task running in something() is not cancelled.  From the POV of
    something(), the cancellation did not happen.  But its caller is
    still cancelled, so the yield-from expression still raises
    CancelledError.  Note: If something() is cancelled by other means
    this will still cancel shield().

    If you want to completely ignore cancellation (not recommended)
    you can combine shield() with a try/except clause, as follows:

        task = asyncio.create_task(something())
        try:
            res = await shield(task)
        except CancelledError:
            res = None

    Save a reference to tasks passed to this function, to avoid
    a task disappearing mid-execution. The event loop only keeps
    weak references to tasks. A task that isn't referenced elsewhere
    may get garbage collected at any time, even before it's done.
    """
    inner = _ensure_future(arg)
    if inner.done():
        return inner
    else:
        loop = futures._get_loop(inner)
        outer = loop.create_future()
        def _inner_done_callback(inner):
            if outer.cancelled():
                if not inner.cancelled():
                    inner.exception()
                return None
            elif inner.cancelled():
                outer.cancel()
                return None
            else:
                exc = inner.exception()
                if exc is not None:
                    outer.set_exception(exc)
                    return None
                else:
                    outer.set_result(inner.result())
        def _outer_done_callback(outer):
            if not inner.done():
                inner.remove_done_callback(_inner_done_callback)
                return None
            else:
                return None
        inner.add_done_callback(_inner_done_callback)
        outer.add_done_callback(_outer_done_callback)
        return outer
def run_coroutine_threadsafe(coro, loop):
    """Submit a coroutine object to a given event loop.

    Return a concurrent.futures.Future to access the result.
    """
    if not coroutines.iscoroutine(coro):
        raise TypeError('A coroutine object is required')
    future = concurrent.futures.Future()
    def callback():
        try:
            futures._chain_future(ensure_future(coro, loop=loop), future)
            return None
        except (SystemExit, KeyboardInterrupt):
            raise
        except BaseException as exc:
            if future.set_running_or_notify_cancel():
                future.set_exception(exc)
            raise
    loop.call_soon_threadsafe(callback)
    return future
_all_tasks = weakref.WeakSet()
_current_tasks = {}
def _register_task(task):
    """Register a new task in asyncio as executed by loop."""
    _all_tasks.add(task)
def _enter_task(loop, task):
    current_task = _current_tasks.get(loop)
    if current_task is not None:
        raise RuntimeError(f'Cannot enter into task {task!r} while another task {current_task!r} is being executed.')
    _current_tasks[loop] = task
def _leave_task(loop, task):
    current_task = _current_tasks.get(loop)
    if current_task is not task:
        raise RuntimeError(f'Leaving task {task!r} does not match the current task {current_task!r}.')
    del _current_tasks[loop]
def _unregister_task(task):
    """Unregister a task."""
    _all_tasks.discard(task)
_py_register_task = _register_task
_py_unregister_task = _unregister_task
_py_enter_task = _enter_task
_py_leave_task = _leave_task
try:
    from _asyncio import _register_task, _unregister_task, _enter_task, _leave_task, _all_tasks, _current_tasks
    _c_register_task = _register_task
    _c_unregister_task = _unregister_task
    _c_enter_task = _enter_task
    _c_leave_task = _leave_task
except ImportError:
    pass
