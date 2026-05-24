"""Object pool for memory reuse in claw-mem v3.4.0.

Provides a generic object pool with context manager support
to reduce GC pressure from frequent allocations.
"""

from contextlib import contextmanager
from typing import Callable, Generic, List, TypeVar

T = TypeVar("T")


class ObjectPool(Generic[T]):
    """Generic object pool for reuse.

    Maintains a pool of pre-created objects. Objects are
    acquired via context manager and returned when done.

    Attributes:
        _factory: Callable that creates new objects.
        _max_size: Maximum pool capacity.
        _pool: Internal object storage.

    Example:
        >>> pool = ObjectPool(list, max_size=10)
        >>> with pool.acquire() as obj:
        ...     obj.append(1)
        ...     print(obj)
        [1]
    """

    def __init__(
        self, factory: Callable[[], T], max_size: int = 100
    ) -> None:
        """Initialize the object pool.

        Args:
            factory: Callable that creates new objects when pool is empty.
            max_size: Maximum number of objects to keep in the pool.
        """
        self._factory = factory
        self._max_size = max_size
        self._pool: List[T] = []

    @contextmanager
    def acquire(self) -> T:
        """Acquire an object from the pool.

        Returns an existing object if available, otherwise
        creates a new one. The object is returned to the
        pool when the context exits.

        Yields:
            An object from the pool or a newly created one.
        """
        if self._pool:
            obj = self._pool.pop()
        else:
            obj = self._factory()

        try:
            yield obj
        finally:
            if len(self._pool) < self._max_size:
                self._pool.append(obj)

    def clear(self) -> None:
        """Clear all objects from the pool."""
        self._pool.clear()

    @property
    def size(self) -> int:
        """Current number of objects in the pool.

        Returns:
            Pool size.
        """
        return len(self._pool)
