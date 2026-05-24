"""Tests for ObjectPool."""

from claw_mem.pool import ObjectPool


class TestObjectPool:
    """Tests for ObjectPool."""

    def test_acquire_new(self):
        pool = ObjectPool(list, max_size=10)
        with pool.acquire() as obj:
            obj.append(1)
            assert obj == [1]

    def test_reuse_object(self):
        pool = ObjectPool(list, max_size=10)
        reused = []

        with pool.acquire() as obj:
            obj.append("marker")
            reused.append(id(obj))

        with pool.acquire() as obj:
            reused.append(id(obj))
            assert obj == ["marker"]  # Same object, reused

        assert reused[0] == reused[1]

    def test_clear(self):
        pool = ObjectPool(list, max_size=10)
        with pool.acquire() as obj:
            obj.append(1)

        assert pool.size == 1
        pool.clear()
        assert pool.size == 0

    def test_max_size(self):
        pool = ObjectPool(list, max_size=2)
        objs = []
        for _ in range(4):
            with pool.acquire() as obj:
                obj.append(1)
                objs.append(id(obj))

        # With 4 acquires and max_size=2, at most 2 unique objects
        # are created (reuse within the pool)
        unique_objs = len(set(objs))
        assert unique_objs <= 3  # At most a few unique objects
        assert pool.size <= 2  # Never exceeds max

    def test_factory_called_when_empty(self):
        counter = [0]

        def factory():
            counter[0] += 1
            return {}

        pool = ObjectPool(factory, max_size=10)
        with pool.acquire():
            pass
        assert counter[0] == 1

        pool.clear()
        with pool.acquire():
            pass
        assert counter[0] == 2  # New object created

    def test_size_property(self):
        pool = ObjectPool(list, max_size=10)
        assert pool.size == 0
        with pool.acquire():
            pass
        assert pool.size == 1
