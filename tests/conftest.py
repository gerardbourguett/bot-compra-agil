"""
Pytest configuration and fixtures for CompraAgil tests.
"""
import os
import sys
import pytest

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

# Load environment variables for tests
from dotenv import load_dotenv
load_dotenv()


# ==================== FIXTURES ====================

@pytest.fixture(scope="session")
def db_connection():
    """
    Provides a database connection for the test session.
    Uses the same database as the application.
    """
    import database_extended as db
    conn = db.get_connection()
    yield conn
    conn.close()


@pytest.fixture
def sample_licitacion():
    """Sample licitacion data for testing."""
    return {
        'codigo': 'TEST-2024-001',
        'nombre': 'Adquisición de equipos computacionales',
        'organismo': 'Municipalidad de Prueba',
        'monto_disponible': 5000000,
        'moneda': 'CLP',
        'fecha_cierre': '2024-12-31T23:59:00',
        'estado': 'Publicada',
        'cantidad_proveedores_cotizando': 3
    }


@pytest.fixture
def sample_perfil_empresa():
    """Sample empresa profile for testing."""
    return {
        'nombre_empresa': 'Empresa Test SpA',
        'tipo_negocio': 'Tecnología',
        'productos_servicios': 'Venta de computadores y servicios TI',
        'palabras_clave': 'computadores, notebooks, servidores',
        'capacidad_entrega_dias': 15,
        'ubicacion': 'Santiago',
        'experiencia_anos': 5,
        'certificaciones': 'ISO 9001'
    }


@pytest.fixture
def mock_redis(monkeypatch):
    """
    Mock Redis for tests that don't need real Redis.
    """
    class MockRedis:
        def __init__(self):
            self._store = {}
        
        def get(self, key):
            return self._store.get(key)
        
        def set(self, key, value, ex=None):
            self._store[key] = value
            return True
        
        def setex(self, key, time, value):
            self._store[key] = value
            return True
        
        def delete(self, *keys):
            count = 0
            for key in keys:
                if key in self._store:
                    del self._store[key]
                    count += 1
            return count
        
        def keys(self, pattern):
            import fnmatch
            return [k for k in self._store.keys() if fnmatch.fnmatch(k, pattern.replace('*', '*'))]
        
        def ping(self):
            return True
        
        def incr(self, key):
            self._store[key] = self._store.get(key, 0) + 1
            return self._store[key]
        
        def expire(self, key, seconds):
            return True
        
        def ttl(self, key):
            return 60
        
        def info(self, section=None):
            return {
                'keyspace_hits': 100,
                'keyspace_misses': 10,
                'used_memory_human': '1M',
                'connected_clients': 1,
                'used_memory': 1024000
            }
        
        def flushdb(self):
            self._store.clear()
            return True
    
    mock = MockRedis()
    
    # Patch redis_cache module
    try:
        import redis_cache
        monkeypatch.setattr(redis_cache, 'redis_client', mock)
        monkeypatch.setattr(redis_cache, 'REDIS_AVAILABLE', True)
    except ImportError:
        pass
    
    return mock


@pytest.fixture
def api_client():
    """
    Provides a TestClient for API testing.
    """
    from fastapi.testclient import TestClient
    
    # Import the app - need to handle path
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
    from api_backend_v3 import app
    
    return TestClient(app)


# ==================== MARKERS ====================

def pytest_configure(config):
    """Configure custom markers."""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line(
        "markers", "integration: marks tests that require external services"
    )
    config.addinivalue_line(
        "markers", "unit: marks pure unit tests"
    )


# ==================== HELPERS ====================

def pytest_collection_modifyitems(config, items):
    """
    Automatically mark tests based on their location/name.
    """
    for item in items:
        # Mark tests in test_api_*.py as integration
        if "test_api" in item.nodeid:
            item.add_marker(pytest.mark.integration)
        
        # Mark tests with 'slow' in name
        if "slow" in item.name.lower():
            item.add_marker(pytest.mark.slow)
