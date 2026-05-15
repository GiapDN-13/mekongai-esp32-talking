"""Tests for core.utils.cache — CacheEntry, GlobalCacheManager."""

import time
from unittest.mock import patch, MagicMock
from core.utils.cache.strategies import CacheEntry, CacheStrategy
from core.utils.cache.config import CacheConfig, CacheType
from core.utils.cache.manager import GlobalCacheManager


class TestCacheEntry:
    def test_not_expired_without_ttl(self):
        entry = CacheEntry(value="x", timestamp=time.time())
        assert entry.is_expired() is False

    def test_not_expired_within_ttl(self):
        entry = CacheEntry(value="x", timestamp=time.time(), ttl=60)
        assert entry.is_expired() is False

    def test_expired(self):
        entry = CacheEntry(value="x", timestamp=time.time() - 10, ttl=5)
        assert entry.is_expired() is True

    def test_touch_increments_access(self):
        entry = CacheEntry(value="x", timestamp=time.time())
        assert entry.access_count == 0
        entry.touch()
        assert entry.access_count == 1
        entry.touch()
        assert entry.access_count == 2


class TestGlobalCacheManager:
    def setup_method(self):
        self.cm = GlobalCacheManager()
        # Prevent logger from importing the real config
        self.cm._logger = MagicMock()

    def test_set_and_get(self):
        self.cm.set(CacheType.LOCATION, "key1", "value1")
        assert self.cm.get(CacheType.LOCATION, "key1") == "value1"

    def test_get_nonexistent_returns_none(self):
        assert self.cm.get(CacheType.LOCATION, "nope") is None

    def test_get_nonexistent_cache_type_returns_none(self):
        assert self.cm.get(CacheType.WEATHER, "anything") is None

    def test_ttl_expiration(self):
        self.cm.set(CacheType.LOCATION, "k", "v", ttl=0.01)
        time.sleep(0.05)
        assert self.cm.get(CacheType.LOCATION, "k") is None

    def test_lru_eviction(self):
        config = CacheConfig(strategy=CacheStrategy.LRU, ttl=None, max_size=3)
        cache_name = self.cm._get_cache_name(CacheType.INTENT, namespace="lru_test")
        self.cm._get_or_create_cache(cache_name, config)

        for i in range(4):
            self.cm.set(CacheType.INTENT, f"k{i}", f"v{i}", namespace="lru_test")

        assert self.cm.get(CacheType.INTENT, "k0", namespace="lru_test") is None
        assert self.cm.get(CacheType.INTENT, "k3", namespace="lru_test") == "v3"

    def test_delete(self):
        self.cm.set(CacheType.LOCATION, "del_me", "bye")
        assert self.cm.delete(CacheType.LOCATION, "del_me") is True
        assert self.cm.get(CacheType.LOCATION, "del_me") is None

    def test_delete_nonexistent(self):
        assert self.cm.delete(CacheType.LOCATION, "nope") is False

    def test_stats_tracking_hits_and_misses(self):
        self.cm.set(CacheType.LOCATION, "s", "v")
        self.cm.get(CacheType.LOCATION, "s")  # hit
        self.cm.get(CacheType.LOCATION, "miss")  # miss
        assert self.cm._stats["hits"] >= 1
        assert self.cm._stats["misses"] >= 1

    def test_namespace_isolation(self):
        self.cm.set(CacheType.LOCATION, "k", "ns1", namespace="a")
        self.cm.set(CacheType.LOCATION, "k", "ns2", namespace="b")
        assert self.cm.get(CacheType.LOCATION, "k", namespace="a") == "ns1"
        assert self.cm.get(CacheType.LOCATION, "k", namespace="b") == "ns2"

    def test_clear(self):
        self.cm.set(CacheType.WEATHER, "w1", "sunny")
        self.cm.clear(CacheType.WEATHER)
        assert self.cm.get(CacheType.WEATHER, "w1") is None
