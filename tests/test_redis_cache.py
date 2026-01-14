"""
Tests for redis_cache.py - Caching layer module.
"""
import pytest


class TestRedisCacheModule:
    """Tests for redis_cache module basics."""
    
    def test_module_imports(self):
        """Redis cache module should import successfully."""
        import redis_cache
        assert redis_cache is not None
    
    def test_redis_available_is_boolean(self):
        """REDIS_AVAILABLE should be a boolean."""
        import redis_cache
        assert isinstance(redis_cache.REDIS_AVAILABLE, bool)
    
    def test_cache_ttl_dict_exists(self):
        """CACHE_TTL should be a dictionary with timedelta values."""
        import redis_cache
        from datetime import timedelta
        
        assert hasattr(redis_cache, 'CACHE_TTL')
        assert isinstance(redis_cache.CACHE_TTL, dict)
        
        for key, value in redis_cache.CACHE_TTL.items():
            assert isinstance(value, timedelta), f"{key} should be timedelta"


class TestGetCacheKey:
    """Tests for get_cache_key function."""
    
    def test_simple_key(self):
        """Should generate simple key with just prefix."""
        import redis_cache
        
        key = redis_cache.get_cache_key('stats')
        assert key == 'stats'
    
    def test_key_with_args(self):
        """Should generate key with positional args."""
        import redis_cache
        
        key = redis_cache.get_cache_key('licitacion', '123', 'detalle')
        assert key == 'licitacion:123:detalle'
    
    def test_key_with_kwargs(self):
        """Should generate key with keyword args."""
        import redis_cache
        
        key = redis_cache.get_cache_key('search', query='laptop', page=1)
        assert 'search' in key
        assert 'query:laptop' in key
        assert 'page:1' in key
    
    def test_key_ignores_none_values(self):
        """Should ignore None values in args."""
        import redis_cache
        
        key = redis_cache.get_cache_key('test', None, 'value', none_param=None)
        assert 'None' not in key
        assert 'value' in key


class TestRateLimiter:
    """Tests for RateLimiter class."""
    
    def test_rate_limiter_creation(self):
        """RateLimiter should be creatable with params."""
        import redis_cache
        
        limiter = redis_cache.RateLimiter(max_requests=10, window=30)
        assert limiter.max_requests == 10
        assert limiter.window == 30
    
    def test_rate_limiter_default_values(self):
        """RateLimiter should have sensible defaults."""
        import redis_cache
        
        limiter = redis_cache.RateLimiter()
        assert limiter.max_requests == 100
        assert limiter.window == 60
    
    def test_rate_limiters_dict_exists(self):
        """Pre-configured rate_limiters dict should exist."""
        import redis_cache
        
        assert hasattr(redis_cache, 'rate_limiters')
        assert 'global' in redis_cache.rate_limiters
        assert 'ml' in redis_cache.rate_limiters
        assert 'search' in redis_cache.rate_limiters


class TestCacheWithMock:
    """Tests using mocked Redis."""
    
    def test_is_allowed_returns_true_when_under_limit(self, mock_redis):
        """is_allowed should return True when under limit."""
        import redis_cache
        
        limiter = redis_cache.RateLimiter(max_requests=10, window=60)
        allowed, info = limiter.is_allowed('test_key')
        
        assert allowed is True
        assert 'limit' in info or 'rate_limit' in info or 'error' not in info
    
    def test_get_cache_stats_with_mock(self, mock_redis):
        """get_cache_stats should return stats dict."""
        import redis_cache
        
        stats = redis_cache.get_cache_stats()
        
        assert isinstance(stats, dict)
        assert 'available' in stats
    
    def test_invalidate_cache_with_mock(self, mock_redis):
        """invalidate_cache should work with mock."""
        import redis_cache
        
        # Add some keys
        mock_redis.set('test:1', 'value1')
        mock_redis.set('test:2', 'value2')
        mock_redis.set('other:1', 'value3')
        
        # Invalidate test:* pattern
        count = redis_cache.invalidate_cache('test:*')
        
        # Should have deleted the test keys
        assert mock_redis.get('test:1') is None
        assert mock_redis.get('test:2') is None
        # Other key should remain
        assert mock_redis.get('other:1') == 'value3'
    
    def test_clear_all_cache_with_mock(self, mock_redis):
        """clear_all_cache should clear everything."""
        import redis_cache
        
        # Add some keys
        mock_redis.set('key1', 'value1')
        mock_redis.set('key2', 'value2')
        
        result = redis_cache.clear_all_cache()
        
        assert result is True
        assert mock_redis.get('key1') is None
        assert mock_redis.get('key2') is None


class TestCacheDecorators:
    """Tests for cache decorator functions."""
    
    def test_cache_response_decorator_exists(self):
        """cache_response decorator should exist."""
        import redis_cache
        
        assert hasattr(redis_cache, 'cache_response')
        assert callable(redis_cache.cache_response)
    
    def test_cache_response_sync_decorator_exists(self):
        """cache_response_sync decorator should exist."""
        import redis_cache
        
        assert hasattr(redis_cache, 'cache_response_sync')
        assert callable(redis_cache.cache_response_sync)
    
    def test_sync_decorator_with_disabled_cache(self):
        """Decorator should work when cache is disabled."""
        import redis_cache
        
        @redis_cache.cache_response_sync('test', enabled=False)
        def test_function(x):
            return x * 2
        
        result = test_function(5)
        assert result == 10
