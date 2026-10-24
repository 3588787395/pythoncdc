# Source Generated with Decompyle++ (Python version)
# File: _synchronization.cpython-311.pyc (Python 3.11)

from __future__ import annotations
import math
from collections import deque
from collections.abc import Callable
from dataclasses import dataclass
from types import TracebackType
from typing import TypeVar
from ..lowlevel import checkpoint_if_cancelled
from ._eventloop import get_async_backend
from ._exceptions import BusyResourceError, NoEventLoopError
from ._tasks import CancelScope
from ._testing import TaskInfo, get_current_task
T = TypeVar('T')
@dataclass(frozen=True)
class EventStatistics:
    __doc__ = """
    :ivar int tasks_waiting: number of tasks waiting on :meth:`~.Event.wait`
    """
    tasks_waiting: 'int'
@dataclass(frozen=True)
class CapacityLimiterStatistics:
    __doc__ = """
    :ivar int borrowed_tokens: number of tokens currently borrowed by tasks
    :ivar float total_tokens: total number of available tokens
    :ivar tuple borrowers: tasks or other objects currently holding tokens borrowed from
        this limiter
    :ivar int tasks_waiting: number of tasks waiting on
        :meth:`~.CapacityLimiter.acquire` or
        :meth:`~.CapacityLimiter.acquire_on_behalf_of`
    """
    borrowed_tokens: 'int'
    total_tokens: 'float'
    borrowers: 'tuple[object, ...]'
    tasks_waiting: 'int'
@dataclass(frozen=True)
class LockStatistics:
    __doc__ = """
    :ivar bool locked: flag indicating if this lock is locked or not
    :ivar ~anyio.TaskInfo owner: task currently holding the lock (or ``None`` if the
        lock is not held by any task)
    :ivar int tasks_waiting: number of tasks waiting on :meth:`~.Lock.acquire`
    """
    locked: 'bool'
    owner: 'TaskInfo | None'
    tasks_waiting: 'int'
@dataclass(frozen=True)
class ConditionStatistics:
    __doc__ = """
    :ivar int tasks_waiting: number of tasks blocked on :meth:`~.Condition.wait`
    :ivar ~anyio.LockStatistics lock_statistics: statistics of the underlying
        :class:`~.Lock`
    """
    tasks_waiting: 'int'
    lock_statistics: 'LockStatistics'
@dataclass(frozen=True)
class SemaphoreStatistics:
    __doc__ = """
    :ivar int tasks_waiting: number of tasks waiting on :meth:`~.Semaphore.acquire`

    """
    tasks_waiting: 'int'
class Event:
    def __new__(cls):
        try:
            return get_async_backend().create_event()
        except NoEventLoopError:
            return EventAdapter()
    def set(self):
        """Set the flag, notifying all listeners."""
        raise NotImplementedError
    def is_set(self):
        """Return ``True`` if the flag is set, ``False`` if not."""
        raise NotImplementedError
    async def wait(self):
        """
        Wait until the flag has been set.

        If the flag has already been set when this method is called, it returns
        immediately.

        """
        raise NotImplementedError
    def statistics(self):
        """Return statistics about the current state of this event."""
        raise NotImplementedError
class EventAdapter(Event):
    _internal_event: 'Event | None' = None
    _is_set: 'bool' = False
    def __new__(cls):
        return object.__new__(cls)
    @property
    def _event(self):
        if self._internal_event is None:
            self._internal_event = get_async_backend().create_event()
            if self._is_set:
                self._internal_event.set()
        return self._internal_event
    def set(self):
        if self._internal_event is None:
            self._is_set = True
            return None
        else:
            self._event.set()
    def is_set(self):
        if self._internal_event is None:
            return self._is_set
        else:
            return self._internal_event.is_set()
    async def wait(self):
        await self._event.wait()
    def statistics(self):
        if self._internal_event is None:
            return EventStatistics(tasks_waiting=0)
        else:
            return self._internal_event.statistics()
class Lock:
    def __new__(cls, *, fast_acquire=False):
        try:
            return get_async_backend().create_lock(fast_acquire=fast_acquire)
        except NoEventLoopError:
            return LockAdapter(fast_acquire=fast_acquire)
    async def __aenter__(self):
        await self.acquire()
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        self.release()
    async def acquire(self):
        """Acquire the lock."""
        raise NotImplementedError
    def acquire_nowait(self):
        """
        Acquire the lock, without blocking.

        :raises ~anyio.WouldBlock: if the operation would block

        """
        raise NotImplementedError
    def release(self):
        """Release the lock."""
        raise NotImplementedError
    def locked(self):
        """Return True if the lock is currently held."""
        raise NotImplementedError
    def statistics(self):
        """
        Return statistics about the current state of this lock.

        .. versionadded:: 3.0
        """
        raise NotImplementedError
class LockAdapter(Lock):
    _internal_lock: 'Lock | None' = None
    def __new__(cls, *, fast_acquire=False):
        return object.__new__(cls)
    def __init__(self, *, fast_acquire=False):
        self._fast_acquire = fast_acquire
    @property
    def _lock(self):
        if self._internal_lock is None:
            self._internal_lock = get_async_backend().create_lock(fast_acquire=self._fast_acquire)
        return self._internal_lock
    async def __aenter__(self):
        await self._lock.acquire()
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self._internal_lock is not None:
            self._internal_lock.release()
            return None
        else:
            return None
    async def acquire(self):
        """Acquire the lock."""
        await self._lock.acquire()
    def acquire_nowait(self):
        """
        Acquire the lock, without blocking.

        :raises ~anyio.WouldBlock: if the operation would block

        """
        self._lock.acquire_nowait()
    def release(self):
        """Release the lock."""
        self._lock.release()
    def locked(self):
        """Return True if the lock is currently held."""
        return self._lock.locked()
    def statistics(self):
        """
        Return statistics about the current state of this lock.

        .. versionadded:: 3.0

        """
        if self._internal_lock is None:
            return LockStatistics(False, None, 0)
        else:
            return self._internal_lock.statistics()
class Condition:
    _owner_task: 'TaskInfo | None' = None
    def __init__(self, lock=None):
        self._lock = lock or Lock()
        self._waiters = deque()
    async def __aenter__(self):
        await self.acquire()
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        self.release()
    def _check_acquired(self):
        if self._owner_task != get_current_task():
            raise RuntimeError('The current task is not holding the underlying lock')
    async def acquire(self):
        """Acquire the underlying lock."""
        await self._lock.acquire()
        self._owner_task = get_current_task()
    def acquire_nowait(self):
        """
        Acquire the underlying lock, without blocking.

        :raises ~anyio.WouldBlock: if the operation would block

        """
        self._lock.acquire_nowait()
        self._owner_task = get_current_task()
    def release(self):
        """Release the underlying lock."""
        self._lock.release()
    def locked(self):
        """Return True if the lock is set."""
        return self._lock.locked()
    def notify(self, n=1):
        """Notify exactly n listeners."""
        self._check_acquired()
        for _ in range(n):
            try:
                event = self._waiters.popleft()
            except IndexError:
                return None
            event.set()
    def notify_all(self):
        """Notify all the listeners."""
        self._check_acquired()
        for event in self._waiters:
            event.set()
        self._waiters.clear()
    async def wait(self):
        """Wait for a notification."""
        await checkpoint_if_cancelled()
        self._check_acquired()
        event = Event()
        self._waiters.append(event)
        self.release()
        try:
            await event.wait()
        except BaseException:
            if not event.is_set():
                self._waiters.remove(event)
            elif self._waiters:
                self._waiters.popleft().set()
            raise
        finally:
            with CancelScope(shield=True):
                await self.acquire()
                return None
    async def wait_for(self, predicate):
        """
        Wait until a predicate becomes true.

        :param predicate: a callable that returns a truthy value when the condition is
            met
        :return: the result of the predicate

        .. versionadded:: 4.11.0

        """
        while not (result := predicate()):
            await self.wait()
        return result
    def statistics(self):
        """
        Return statistics about the current state of this condition.

        .. versionadded:: 3.0
        """
        return ConditionStatistics(len(self._waiters), self._lock.statistics())
class Semaphore:
    def __new__(cls, initial_value, *, max_value=None, fast_acquire=False):
        try:
            return get_async_backend().create_semaphore(initial_value, max_value=max_value, fast_acquire=fast_acquire)
        except NoEventLoopError:
            return SemaphoreAdapter(initial_value, max_value=max_value)
    def __init__(self, initial_value, *, max_value=None, fast_acquire=False):
        if not isinstance(initial_value, int):
            raise TypeError('initial_value must be an integer')
        elif initial_value < 0:
            raise ValueError('initial_value must be >= 0')
        elif max_value is not None:
            if not isinstance(max_value, int):
                raise TypeError('max_value must be an integer or None')
            elif max_value < initial_value:
                raise ValueError('max_value must be equal to or higher than initial_value')
        self._fast_acquire = fast_acquire
    async def __aenter__(self):
        await self.acquire()
        return self
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        self.release()
    async def acquire(self):
        """Decrement the semaphore value, blocking if necessary."""
        raise NotImplementedError
    def acquire_nowait(self):
        """
        Acquire the underlying lock, without blocking.

        :raises ~anyio.WouldBlock: if the operation would block

        """
        raise NotImplementedError
    def release(self):
        """Increment the semaphore value."""
        raise NotImplementedError
    @property
    def value(self):
        """The current value of the semaphore."""
        raise NotImplementedError
    @property
    def max_value(self):
        """The maximum value of the semaphore."""
        raise NotImplementedError
    def statistics(self):
        """
        Return statistics about the current state of this semaphore.

        .. versionadded:: 3.0
        """
        raise NotImplementedError
class SemaphoreAdapter(Semaphore):
    _internal_semaphore: 'Semaphore | None' = None
    def __new__(cls, initial_value, *, max_value=None, fast_acquire=False):
        return object.__new__(cls)
    def __init__(self, initial_value, *, max_value=None, fast_acquire=False):
        super().__init__(initial_value, max_value=max_value, fast_acquire=fast_acquire)
        self._initial_value = initial_value
        self._max_value = max_value
    @property
    def _semaphore(self):
        if self._internal_semaphore is None:
            self._internal_semaphore = get_async_backend().create_semaphore(self._initial_value, max_value=self._max_value)
        return self._internal_semaphore
    async def acquire(self):
        await self._semaphore.acquire()
    def acquire_nowait(self):
        self._semaphore.acquire_nowait()
    def release(self):
        self._semaphore.release()
    @property
    def value(self):
        if self._internal_semaphore is None:
            return self._initial_value
        else:
            return self._semaphore.value
    @property
    def max_value(self):
        return self._max_value
    def statistics(self):
        if self._internal_semaphore is None:
            return SemaphoreStatistics(tasks_waiting=0)
        else:
            return self._semaphore.statistics()
class CapacityLimiter:
    def __new__(cls, total_tokens):
        try:
            return get_async_backend().create_capacity_limiter(total_tokens)
        except NoEventLoopError:
            return CapacityLimiterAdapter(total_tokens)
    async def __aenter__(self):
        raise NotImplementedError
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        raise NotImplementedError
    @property
    def total_tokens(self):
        """
        The total number of tokens available for borrowing.

        This is a read-write property. If the total number of tokens is increased, the
        proportionate number of tasks waiting on this limiter will be granted their
        tokens.

        .. versionchanged:: 3.0
            The property is now writable.
        .. versionchanged:: 4.12
            The value can now be set to 0.

        """
        raise NotImplementedError
    @total_tokens.setter
    def total_tokens(self, value):
        raise NotImplementedError
    @property
    def borrowed_tokens(self):
        """The number of tokens that have currently been borrowed."""
        raise NotImplementedError
    @property
    def available_tokens(self):
        """The number of tokens currently available to be borrowed"""
        raise NotImplementedError
    def acquire_nowait(self):
        """
        Acquire a token for the current task without waiting for one to become
        available.

        :raises ~anyio.WouldBlock: if there are no tokens available for borrowing

        """
        raise NotImplementedError
    def acquire_on_behalf_of_nowait(self, borrower):
        """
        Acquire a token without waiting for one to become available.

        :param borrower: the entity borrowing a token
        :raises ~anyio.WouldBlock: if there are no tokens available for borrowing

        """
        raise NotImplementedError
    async def acquire(self):
        """
        Acquire a token for the current task, waiting if necessary for one to become
        available.

        """
        raise NotImplementedError
    async def acquire_on_behalf_of(self, borrower):
        """
        Acquire a token, waiting if necessary for one to become available.

        :param borrower: the entity borrowing a token

        """
        raise NotImplementedError
    def release(self):
        """
        Release the token held by the current task.

        :raises RuntimeError: if the current task has not borrowed a token from this
            limiter.

        """
        raise NotImplementedError
    def release_on_behalf_of(self, borrower):
        """
        Release the token held by the given borrower.

        :raises RuntimeError: if the borrower has not borrowed a token from this
            limiter.

        """
        raise NotImplementedError
    def statistics(self):
        """
        Return statistics about the current state of this limiter.

        .. versionadded:: 3.0

        """
        raise NotImplementedError
class CapacityLimiterAdapter(CapacityLimiter):
    _internal_limiter: 'CapacityLimiter | None' = None
    def __new__(cls, total_tokens):
        return object.__new__(cls)
    def __init__(self, total_tokens):
        self.total_tokens = total_tokens
    @property
    def _limiter(self):
        if self._internal_limiter is None:
            self._internal_limiter = get_async_backend().create_capacity_limiter(self._total_tokens)
        return self._internal_limiter
    async def __aenter__(self):
        await self._limiter.__aenter__()
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        return await self._limiter.__aexit__(exc_type, exc_val, exc_tb)
    @property
    def total_tokens(self):
        if self._internal_limiter is None:
            return self._total_tokens
        else:
            return self._internal_limiter.total_tokens
    @total_tokens.setter
    def total_tokens(self, value):
        if not isinstance(value, int) and value is not math.inf:
            raise TypeError('total_tokens must be an int or math.inf')
        if value < 1:
            raise ValueError('total_tokens must be >= 1')
        elif self._internal_limiter is None:
            self._total_tokens = value
            return None
        else:
            self._limiter.total_tokens = value
    @property
    def borrowed_tokens(self):
        if self._internal_limiter is None:
            return 0
        else:
            return self._internal_limiter.borrowed_tokens
    @property
    def available_tokens(self):
        if self._internal_limiter is None:
            return self._total_tokens
        else:
            return self._internal_limiter.available_tokens
    def acquire_nowait(self):
        self._limiter.acquire_nowait()
    def acquire_on_behalf_of_nowait(self, borrower):
        self._limiter.acquire_on_behalf_of_nowait(borrower)
    async def acquire(self):
        await self._limiter.acquire()
    async def acquire_on_behalf_of(self, borrower):
        await self._limiter.acquire_on_behalf_of(borrower)
    def release(self):
        self._limiter.release()
    def release_on_behalf_of(self, borrower):
        self._limiter.release_on_behalf_of(borrower)
    def statistics(self):
        if self._internal_limiter is None:
            return CapacityLimiterStatistics(borrowed_tokens=0, total_tokens=self.total_tokens, borrowers=(), tasks_waiting=0)
        else:
            return self._internal_limiter.statistics()
class ResourceGuard:
    __doc__ = """
    A context manager for ensuring that a resource is only used by a single task at a
    time.

    Entering this context manager while the previous has not exited it yet will trigger
    :exc:`BusyResourceError`.

    :param action: the action to guard against (visible in the :exc:`BusyResourceError`
        when triggered, e.g. "Another task is already {action} this resource")

    .. versionadded:: 4.1
    """
    __slots__ = ('action', '_guarded')
    def __init__(self, action='using'):
        self.action = action
        self._guarded = False
    def __enter__(self):
        if self._guarded:
            raise BusyResourceError(self.action)
        self._guarded = True
    def __exit__(self, exc_type, exc_val, exc_tb):
        self._guarded = False
