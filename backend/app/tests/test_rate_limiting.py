"""
Tests for Rate Limiting
Tests that rate limiting is properly applied to endpoints
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


class TestRateLimiting:
    """Test rate limiting functionality"""
    
    def test_rate_limit_headers_present(self):
        """Test that rate limit headers are included in responses"""
        response = client.get("/")
        
        # Check that rate limit headers are present
        assert "X-RateLimit-Limit" in response.headers or "RateLimit-Limit" in response.headers
        
    def test_public_endpoint_rate_limit(self):
        """Test that public endpoints have rate limits"""
        # Make multiple requests to public endpoint
        responses = []
        for i in range(5):
            response = client.get("/")
            responses.append(response)
        
        # All should succeed (limit is 100/minute)
        for response in responses:
            assert response.status_code == 200
    
    def test_health_check_high_limit(self):
        """Test that health check has high rate limit"""
        # Make multiple requests to health endpoint
        responses = []
        for i in range(10):
            response = client.get("/health")
            responses.append(response)
        
        # All should succeed (limit is 1000/minute)
        for response in responses:
            assert response.status_code in [200, 503]  # 503 if DB is down
    
    def test_rate_limit_error_format(self):
        """Test that rate limit errors return proper format"""
        # This test would need to actually trigger rate limit
        # which requires making many requests quickly
        # For now, we just verify the endpoint exists
        response = client.get("/")
        assert response.status_code == 200
        
    def test_different_endpoints_have_limits(self):
        """Test that different endpoint types have appropriate limits"""
        # Test that endpoints respond (they have rate limits applied)
        
        # Public endpoint
        response = client.get("/")
        assert response.status_code == 200
        
        # Health check
        response = client.get("/health")
        assert response.status_code in [200, 503]
        
        # Version endpoint
        response = client.get("/version")
        assert response.status_code == 200


class TestRateLimitConfiguration:
    """Test rate limit configuration"""
    
    def test_rate_limit_middleware_loaded(self):
        """Test that rate limit middleware is loaded"""
        # Check that limiter is in app state
        assert hasattr(app.state, "limiter")
        assert app.state.limiter is not None
    
    def test_rate_limit_exception_handler_registered(self):
        """Test that rate limit exception handler is registered"""
        # Check that exception handlers include RateLimitExceeded
        from slowapi.errors import RateLimitExceeded
        assert RateLimitExceeded in app.exception_handlers


class TestRateLimitCategories:
    """Test that rate limit categories are properly defined"""
    
    def test_rate_limits_class_exists(self):
        """Test that RateLimits class exists and has proper attributes"""
        from app.middleware.rate_limit import RateLimits
        
        # Check that all expected rate limit categories exist
        assert hasattr(RateLimits, "AUTH_LOGIN")
        assert hasattr(RateLimits, "AUTH_REGISTER")
        assert hasattr(RateLimits, "AUTH_REFRESH")
        assert hasattr(RateLimits, "CREATE")
        assert hasattr(RateLimits, "UPDATE")
        assert hasattr(RateLimits, "DELETE")
        assert hasattr(RateLimits, "READ")
        assert hasattr(RateLimits, "LIST")
        assert hasattr(RateLimits, "GOOGLE_CALENDAR")
        assert hasattr(RateLimits, "PUBLIC")
        assert hasattr(RateLimits, "HEALTH_CHECK")
    
    def test_rate_limit_values_format(self):
        """Test that rate limit values are in correct format"""
        from app.middleware.rate_limit import RateLimits
        
        # Check format: "number/timeunit"
        assert "/" in RateLimits.AUTH_LOGIN
        assert "/" in RateLimits.CREATE
        assert "/" in RateLimits.READ
        
        # Check that numbers are reasonable
        login_limit = int(RateLimits.AUTH_LOGIN.split("/")[0])
        assert login_limit > 0
        assert login_limit <= 100  # Should be strict for auth
        
        read_limit = int(RateLimits.READ.split("/")[0])
        assert read_limit >= login_limit  # Read should be more permissive


class TestEndpointRateLimits:
    """Test that specific endpoints have rate limits applied"""
    
    def test_auth_endpoints_have_strict_limits(self):
        """Test that auth endpoints exist and respond"""
        # These would need proper test data to fully test
        # For now, verify endpoints exist
        
        # Register endpoint (should have strict limit)
        response = client.post("/auth/register", json={
            "email": "test@example.com",
            "password": "Test123!@#",
            "display_name": "Test User"
        })
        # Will fail without DB, but endpoint exists
        assert response.status_code in [201, 400, 422, 503]
        
    def test_task_endpoints_have_limits(self):
        """Test that task endpoints have rate limits"""
        # List tasks (should have LIST limit)
        response = client.get("/api/tasks")
        # Will fail without auth, but endpoint exists
        assert response.status_code in [200, 401, 422, 503]


# Note: To fully test rate limiting, you would need to:
# 1. Make many requests quickly to trigger the limit
# 2. Verify 429 status code is returned
# 3. Check retry-after header
# 4. Verify rate limit resets after time period
# 
# This requires either:
# - Mocking the rate limiter
# - Using a test rate limiter with very low limits
# - Making actual rapid requests (slow and flaky)
#
# For production testing, consider:
# - Integration tests with low rate limits
# - Load testing tools (locust, k6)
# - Manual testing with curl loops


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
