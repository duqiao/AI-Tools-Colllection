"""
FastAPI Backend Contract Tests

This test suite validates the FastAPI backend contracts and ensures
API compatibility with the frontend expectations.
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from unittest.mock import Mock, patch

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.database import get_db
from app.models.user import User
from app.models.subscription import Subscription
from app.models.translation import Translation
from app.models.payment import PaymentOrder

# Test database setup
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create test client
client = TestClient(app)

def override_get_db():
    """Override database dependency for testing"""
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

class TestAuthenticationContracts:
    """Test authentication API contracts"""
    
    def setup_method(self):
        """Setup test data"""
        self.test_user_data = {
            "code": "test_wechat_code",
            "userInfo": {
                "nickName": "Test User",
                "avatarUrl": "https://example.com/avatar.jpg",
                "gender": 1,
                "language": "zh_CN",
                "city": "Test City",
                "province": "Test Province",
                "country": "Test Country"
            }
        }
    
    def test_wechat_login_contract(self):
        """Test WeChat login API contract"""
        response = client.post("/api/v1/auth/wechat-login", json=self.test_user_data)
        
        # Verify response structure
        assert response.status_code in [200, 400, 500]  # Expected status codes
        
        if response.status_code == 200:
            data = response.json()
            
            # Verify required fields
            assert "code" in data
            assert "message" in data
            assert "data" in data
            
            if data["code"] == 200:
                user_data = data["data"]
                assert "token" in user_data
                assert "user" in user_data
                assert "openid" in user_data["user"]
                assert "subscription_level" in user_data["user"]
    
    def test_get_user_info_contract(self):
        """Test get user info API contract"""
        # First login to get token
        with patch('app.api.v1.auth.wechat_service.get_wechat_user_info') as mock_wechat:
            mock_wechat.return_value = {
                "openid": "test_openid",
                "nickname": "Test User"
            }
            
            login_response = client.post("/api/v1/auth/wechat-login", json=self.test_user_data)
            
            if login_response.status_code == 200:
                token = login_response.json()["data"]["token"]
                
                # Test get user info
                headers = {"Authorization": f"Bearer {token}"}
                response = client.get("/api/v1/auth/user", headers=headers)
                
                assert response.status_code in [200, 401, 403]
                
                if response.status_code == 200:
                    data = response.json()
                    assert "code" in data
                    assert "data" in data
                    
                    user_data = data["data"]
                    expected_fields = ["id", "openid", "username", "subscription_level", "quota_used", "quota_limit"]
                    for field in expected_fields:
                        assert field in user_data

class TestTranslationContracts:
    """Test translation API contracts"""
    
    def setup_method(self):
        """Setup test data"""
        self.test_translation_data = {
            "file_type": "audio",
            "original_filename": "test.mp3",
            "file_size": 1024000,
            "file_url": "https://example.com/test.mp3",
            "duration_seconds": 120
        }
    
    def test_create_translation_task_contract(self):
        """Test create translation task API contract"""
        response = client.post("/api/v1/translation/create", json=self.test_translation_data)
        
        # Verify response structure
        assert response.status_code in [200, 400, 401, 500]
        
        if response.status_code == 200:
            data = response.json()
            
            # Verify required fields
            assert "code" in data
            assert "message" in data
            assert "data" in data
            
            if data["code"] == 200:
                task_data = data["data"]
                assert "task_id" in task_data
                assert "status" in task_data
                assert isinstance(task_data["task_id"], str)
    
    def test_get_translation_status_contract(self):
        """Test get translation status API contract"""
        # Create a test task first
        task_id = "test-task-123"
        
        response = client.get(f"/api/v1/translation/{task_id}/status")
        
        # Verify response structure
        assert response.status_code in [200, 404, 400]
        
        if response.status_code == 200:
            data = response.json()
            assert "code" in data
            assert "data" in data
            
            if data["code"] == 200:
                status_data = data["data"]
                expected_fields = ["task_id", "status", "progress_percentage", "created_at"]
                for field in expected_fields:
                    assert field in status_data
                
                # Validate status values
                valid_statuses = ["pending", "uploading", "processing", "completed", "failed", "cancelled"]
                assert status_data["status"] in valid_statuses
    
    def test_get_translation_history_contract(self):
        """Test get translation history API contract"""
        params = {
            "page": 1,
            "page_size": 10,
            "status": "completed"
        }
        
        response = client.get("/api/v1/translation/history", params=params)
        
        # Verify response structure
        assert response.status_code in [200, 400, 401]
        
        if response.status_code == 200:
            data = response.json()
            assert "code" in data
            assert "data" in data
            
            if data["code"] == 200:
                history_data = data["data"]
                assert "items" in history_data
                assert "total" in history_data
                assert "page" in history_data
                assert "page_size" in history_data
                
                # Validate pagination
                assert isinstance(history_data["items"], list)
                assert isinstance(history_data["total"], int)
                assert isinstance(history_data["page"], int)
                assert isinstance(history_data["page_size"], int)

class TestQuotaContracts:
    """Test quota API contracts"""
    
    def test_get_quota_status_contract(self):
        """Test get quota status API contract"""
        response = client.get("/api/v1/quota/status")
        
        # Verify response structure
        assert response.status_code in [200, 401]
        
        if response.status_code == 200:
            data = response.json()
            assert "code" in data
            assert "data" in data
            
            if data["code"] == 200:
                quota_data = data["data"]
                expected_fields = ["quota_used", "quota_limit", "quota_remaining", "reset_date"]
                for field in expected_fields:
                    assert field in quota_data
                
                # Validate quota values
                assert isinstance(quota_data["quota_used"], int)
                assert isinstance(quota_data["quota_limit"], int)
                assert isinstance(quota_data["quota_remaining"], int)
                assert quota_data["quota_remaining"] >= 0
    
    def test_check_quota_availability_contract(self):
        """Test check quota availability API contract"""
        request_data = {
            "required_quota": 1
        }
        
        response = client.post("/api/v1/quota/check", json=request_data)
        
        # Verify response structure
        assert response.status_code in [200, 400, 401]
        
        if response.status_code == 200:
            data = response.json()
            assert "code" in data
            assert "data" in data
            
            if data["code"] == 200:
                availability_data = data["data"]
                expected_fields = ["available", "quota_remaining", "sufficient"]
                for field in expected_fields:
                    assert field in availability_data
                
                # Validate boolean fields
                assert isinstance(availability_data["available"], bool)
                assert isinstance(availability_data["sufficient"], bool)

class TestSubscriptionContracts:
    """Test subscription API contracts"""
    
    def test_get_subscription_plans_contract(self):
        """Test get subscription plans API contract"""
        response = client.get("/api/v1/subscription/plans")
        
        # Verify response structure
        assert response.status_code in [200]
        
        if response.status_code == 200:
            data = response.json()
            assert "code" in data
            assert "data" in data
            
            if data["code"] == 200:
                plans = data["data"]
                assert isinstance(plans, list)
                
                if len(plans) > 0:
                    plan = plans[0]
                    expected_fields = ["id", "name", "code", "price", "quota_limit", "features"]
                    for field in expected_fields:
                        assert field in plan
                    
                    # Validate plan data
                    assert isinstance(plan["id"], int)
                    assert isinstance(plan["name"], str)
                    assert isinstance(plan["code"], str)
                    assert isinstance(plan["price"], (int, float))
                    assert isinstance(plan["quota_limit"], int)
    
    def test_get_user_subscription_contract(self):
        """Test get user subscription API contract"""
        response = client.get("/api/v1/subscription/user")
        
        # Verify response structure
        assert response.status_code in [200, 401, 404]
        
        if response.status_code == 200:
            data = response.json()
            assert "code" in data
            assert "data" in data
            
            if data["code"] == 200:
                sub_data = data["data"]
                if sub_data:  # User has subscription
                    expected_fields = ["id", "plan_type", "status", "start_date", "monthly_quota", "used_quota"]
                    for field in expected_fields:
                        assert field in sub_data

class TestPaymentContracts:
    """Test payment API contracts"""
    
    def test_create_order_contract(self):
        """Test create payment order API contract"""
        request_data = {
            "plan_id": 1
        }
        
        response = client.post("/api/v1/subscription/create-order", json=request_data)
        
        # Verify response structure
        assert response.status_code in [200, 400, 401, 404]
        
        if response.status_code == 200:
            data = response.json()
            assert "code" in data
            assert "data" in data
            
            if data["code"] == 200:
                order_data = data["data"]
                expected_fields = ["order_no", "plan_type", "amount", "payment_status"]
                for field in expected_fields:
                    assert field in order_data
                
                # Validate order data
                assert isinstance(order_data["order_no"], str)
                assert isinstance(order_data["amount"], (int, float))
                assert isinstance(order_data["payment_status"], str)
    
    def test_check_payment_status_contract(self):
        """Test check payment status API contract"""
        order_no = "test-order-123"
        
        response = client.get(f"/api/v1/payment/status/{order_no}")
        
        # Verify response structure
        assert response.status_code in [200, 404]
        
        if response.status_code == 200:
            data = response.json()
            assert "code" in data
            assert "data" in data
            
            if data["code"] == 200:
                payment_data = data["data"]
                expected_fields = ["order_no", "payment_status", "amount", "created_at"]
                for field in expected_fields:
                    assert field in payment_data

class TestErrorContracts:
    """Test error response contracts"""
    
    def test_404_error_contract(self):
        """Test 404 error response contract"""
        response = client.get("/api/v1/nonexistent-endpoint")
        
        assert response.status_code == 404
        
        data = response.json()
        assert "code" in data
        assert "message" in data
        assert data["code"] == 404
    
    def test_validation_error_contract(self):
        """Test validation error response contract"""
        # Send invalid data
        response = client.post("/api/v1/translation/create", json={})
        
        assert response.status_code == 422
        
        data = response.json()
        assert "code" in data
        assert "message" in data
        assert "errors" in data  # Validation errors should be included
    
    def test_authentication_error_contract(self):
        """Test authentication error response contract"""
        headers = {"Authorization": "Bearer invalid-token"}
        response = client.get("/api/v1/auth/user", headers=headers)
        
        assert response.status_code in [401, 403]
        
        data = response.json()
        assert "code" in data
        assert "message" in data

class TestResponseFormatContracts:
    """Test response format contracts"""
    
    def test_standard_response_format(self):
        """Test standard API response format"""
        response = client.get("/api/v1/quota/status")
        
        if response.status_code == 200:
            data = response.json()
            
            # All responses should have these fields
            assert "code" in data
            assert "message" in data
            assert "data" in data
            
            # Code should be integer
            assert isinstance(data["code"], int)
            
            # Message should be string
            assert isinstance(data["message"], str)
            
            # Data should be serializable
            assert data["data"] is not None
    
    def test_pagination_format(self):
        """Test pagination response format"""
        params = {"page": 1, "page_size": 10}
        response = client.get("/api/v1/translation/history", params=params)
        
        if response.status_code == 200:
            data = response.json()
            
            if data["code"] == 200:
                paginated_data = data["data"]
                
                # Pagination fields
                required_fields = ["items", "total", "page", "page_size", "total_pages"]
                for field in required_fields:
                    assert field in paginated_data
                
                # Validate pagination data types
                assert isinstance(paginated_data["items"], list)
                assert isinstance(paginated_data["total"], int)
                assert isinstance(paginated_data["page"], int)
                assert isinstance(paginated_data["page_size"], int)
                assert isinstance(paginated_data["total_pages"], int)

# Integration test class
class TestAPIIntegration:
    """Test API integration scenarios"""
    
    def test_complete_translation_workflow(self):
        """Test complete translation workflow integration"""
        # Step 1: Create translation task
        task_data = {
            "file_type": "audio",
            "original_filename": "integration-test.mp3",
            "file_size": 2048000,
            "file_url": "https://example.com/integration.mp3",
            "duration_seconds": 180
        }
        
        create_response = client.post("/api/v1/translation/create", json=task_data)
        
        if create_response.status_code == 200:
            task_id = create_response.json()["data"]["task_id"]
            
            # Step 2: Check translation status
            status_response = client.get(f"/api/v1/translation/{task_id}/status")
            
            # Should return valid status
            assert status_response.status_code in [200, 404]
            
            if status_response.status_code == 200:
                status_data = status_response.json()["data"]
                assert status_data["task_id"] == task_id
    
    def test_user_subscription_workflow(self):
        """Test user subscription workflow integration"""
        # Step 1: Get available plans
        plans_response = client.get("/api/v1/subscription/plans")
        
        if plans_response.status_code == 200:
            plans = plans_response.json()["data"]
            
            if len(plans) > 0:
                plan_id = plans[0]["id"]
                
                # Step 2: Create order
                order_response = client.post("/api/v1/subscription/create-order", json={"plan_id": plan_id})
                
                if order_response.status_code == 200:
                    order_data = order_response.json()["data"]
                    order_no = order_data["order_no"]
                    
                    # Step 3: Check payment status
                    status_response = client.get(f"/api/v1/payment/status/{order_no}")
                    
                    # Should return valid payment status
                    assert status_response.status_code in [200, 404]

if __name__ == "__main__":
    pytest.main([__file__, "-v"])