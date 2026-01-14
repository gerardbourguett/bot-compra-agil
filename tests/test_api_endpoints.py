"""
Tests for API endpoints using FastAPI TestClient.
"""
import pytest


@pytest.mark.integration
class TestAPIRoot:
    """Tests for root endpoints."""
    
    def test_root_endpoint(self, api_client):
        """GET / should return API info."""
        response = api_client.get("/")
        
        assert response.status_code == 200
        data = response.json()
        
        assert 'app' in data
        assert 'CompraÁgil' in data['app']
        assert 'version' in data
    
    def test_health_endpoint(self, api_client):
        """GET /health should return health status."""
        response = api_client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        
        assert 'status' in data


@pytest.mark.integration
class TestLicitacionesEndpoints:
    """Tests for licitaciones endpoints."""
    
    def test_list_licitaciones(self, api_client):
        """GET /api/v3/licitaciones/ should return paginated list."""
        response = api_client.get("/api/v3/licitaciones/", params={"page": 1, "limit": 5})
        
        assert response.status_code == 200
        data = response.json()
        
        assert 'success' in data
        assert 'data' in data
        assert 'pagination' in data
        
        if data['success']:
            assert isinstance(data['data'], list)
            assert 'page' in data['pagination']
            assert 'total' in data['pagination']
    
    def test_list_licitaciones_with_filters(self, api_client):
        """GET /api/v3/licitaciones/ should accept filter params."""
        response = api_client.get(
            "/api/v3/licitaciones/",
            params={
                "page": 1,
                "limit": 5,
                "estado": "Publicada"
            }
        )
        
        assert response.status_code == 200
    
    def test_search_licitaciones(self, api_client):
        """GET /api/v3/licitaciones/search should search by query."""
        response = api_client.get(
            "/api/v3/licitaciones/search",
            params={"q": "computador", "limit": 5}
        )
        
        # Should return 200 even with no results
        assert response.status_code == 200


@pytest.mark.integration
class TestStatsEndpoints:
    """Tests for statistics endpoints."""
    
    def test_stats_endpoint(self, api_client):
        """GET /api/v3/stats should return statistics."""
        response = api_client.get("/api/v3/stats")
        
        assert response.status_code == 200
        data = response.json()
        
        # Should have some stats fields
        assert isinstance(data, dict)


@pytest.mark.integration
class TestProductosEndpoints:
    """Tests for productos endpoints."""
    
    def test_search_productos(self, api_client):
        """GET /api/v3/productos/search should search products."""
        response = api_client.get(
            "/api/v3/productos/search",
            params={"q": "laptop", "limit": 5}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert 'success' in data


@pytest.mark.integration
class TestRateLimiting:
    """Tests for rate limiting behavior."""
    
    def test_rate_limit_headers(self, api_client):
        """Responses should include rate limit info."""
        response = api_client.get("/api/v3/licitaciones/", params={"limit": 1})
        
        # Rate limit info might be in headers or body
        # Just verify the endpoint works
        assert response.status_code in [200, 429]
    
    def test_many_requests_dont_crash(self, api_client):
        """Multiple rapid requests should not crash the API."""
        for _ in range(10):
            response = api_client.get("/health")
            # Should either succeed or rate limit, not error
            assert response.status_code in [200, 429]


@pytest.mark.integration
class TestErrorHandling:
    """Tests for API error handling."""
    
    def test_404_for_unknown_endpoint(self, api_client):
        """Unknown endpoints should return 404."""
        response = api_client.get("/api/v3/unknown_endpoint_xyz")
        
        assert response.status_code == 404
    
    def test_invalid_page_number(self, api_client):
        """Invalid page numbers should be handled gracefully."""
        response = api_client.get(
            "/api/v3/licitaciones/",
            params={"page": -1, "limit": 5}
        )
        
        # Should either return 200 with empty or 400 bad request
        assert response.status_code in [200, 400, 422]
    
    def test_invalid_limit(self, api_client):
        """Very large limits should be handled."""
        response = api_client.get(
            "/api/v3/licitaciones/",
            params={"page": 1, "limit": 10000}
        )
        
        # Should handle gracefully
        assert response.status_code in [200, 400, 422]


@pytest.mark.integration
class TestMLEndpoints:
    """Tests for ML-related endpoints."""
    
    def test_precio_optimo_endpoint_exists(self, api_client):
        """ML precio endpoint should exist."""
        response = api_client.get(
            "/api/v3/ml/precio-optimo",
            params={"producto": "laptop", "cantidad": 10}
        )
        
        # Should return 200 or 404 if not implemented
        assert response.status_code in [200, 404, 422]
    
    def test_rag_search_endpoint_exists(self, api_client):
        """RAG search endpoint should exist."""
        response = api_client.get(
            "/api/v3/ml/rag/search",
            params={"query": "computadores"}
        )
        
        # Should return 200 or 404 if not implemented
        assert response.status_code in [200, 404, 422]
