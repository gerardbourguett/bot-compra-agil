"""
Tests for src/config.py - Centralized configuration module.
"""
import os
import pytest


class TestConfigLoading:
    """Tests for configuration loading."""
    
    def test_config_imports_successfully(self):
        """Config module should import without errors."""
        import config
        assert config is not None
    
    def test_gemini_model_has_default(self):
        """GEMINI_MODEL should have a default value."""
        import config
        assert config.GEMINI_MODEL is not None
        assert 'gemini' in config.GEMINI_MODEL.lower()
    
    def test_rate_limits_structure(self):
        """RATE_LIMITS should have expected structure."""
        import config
        
        assert 'global' in config.RATE_LIMITS
        assert 'ml' in config.RATE_LIMITS
        assert 'search' in config.RATE_LIMITS
        
        for name, limits in config.RATE_LIMITS.items():
            assert 'max_requests' in limits
            assert 'window' in limits
            assert isinstance(limits['max_requests'], int)
            assert isinstance(limits['window'], int)
    
    def test_cache_ttl_structure(self):
        """CACHE_TTL should have expected keys."""
        import config
        
        expected_keys = ['stats_general', 'licitacion', 'ml_precio', 'default']
        for key in expected_keys:
            assert key in config.CACHE_TTL, f"Missing key: {key}"
            assert isinstance(config.CACHE_TTL[key], int)
    
    def test_subscription_pricing(self):
        """Subscription pricing should have all tiers."""
        import config
        
        expected_tiers = ['free', 'emprendedor', 'pyme', 'profesional']
        for tier in expected_tiers:
            assert tier in config.SUBSCRIPTION_PRICING_CLP
        
        # Free should be 0
        assert config.SUBSCRIPTION_PRICING_CLP['free'] == 0
        
        # Others should be > 0
        assert config.SUBSCRIPTION_PRICING_CLP['emprendedor'] > 0
        assert config.SUBSCRIPTION_PRICING_CLP['pyme'] > 0
        assert config.SUBSCRIPTION_PRICING_CLP['profesional'] > 0


class TestConfigHelpers:
    """Tests for config helper functions."""
    
    def test_get_rate_limit_existing(self):
        """get_rate_limit should return config for existing key."""
        import config
        
        result = config.get_rate_limit('ml')
        assert 'max_requests' in result
        assert 'window' in result
    
    def test_get_rate_limit_fallback(self):
        """get_rate_limit should fallback to global for unknown key."""
        import config
        
        result = config.get_rate_limit('nonexistent_key')
        expected = config.RATE_LIMITS['global']
        assert result == expected
    
    def test_is_production_default(self):
        """is_production should return False by default."""
        import config
        
        # Unless ENV=production is set, should be False
        if os.getenv('ENV', '').lower() != 'production':
            assert config.is_production() is False


class TestConfigPorts:
    """Tests for port configuration."""
    
    def test_api_port_is_integer(self):
        """API_PORT should be an integer."""
        import config
        assert isinstance(config.API_PORT, int)
        assert config.API_PORT > 0
    
    def test_metrics_port_is_integer(self):
        """METRICS_PORT should be an integer."""
        import config
        assert isinstance(config.METRICS_PORT, int)
        assert config.METRICS_PORT > 0
    
    def test_ports_are_different(self):
        """API and metrics ports should be different."""
        import config
        assert config.API_PORT != config.METRICS_PORT


class TestConfigEnvOverrides:
    """Tests for environment variable overrides."""
    
    def test_gemini_model_env_override(self, monkeypatch):
        """GEMINI_MODEL should be overridable via env."""
        monkeypatch.setenv('GEMINI_MODEL', 'gemini-test-model')
        
        # Need to reload config to pick up new env
        import importlib
        import config
        importlib.reload(config)
        
        assert config.GEMINI_MODEL == 'gemini-test-model'
    
    def test_api_port_env_override(self, monkeypatch):
        """API_PORT should be overridable via env."""
        monkeypatch.setenv('API_PORT', '9999')
        
        import importlib
        import config
        importlib.reload(config)
        
        assert config.API_PORT == 9999
