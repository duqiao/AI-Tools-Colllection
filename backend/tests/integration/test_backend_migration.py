"""
Backend Integration Tests

This test suite validates the integration between the FastAPI backend
components and ensures data flow integrity.
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from unittest.mock import Mock, patch, AsyncMock
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.database import get_db
from app.models.user import User
from app.models.subscription import Subscription
from app.models.translation import Translation
from app.models.payment import PaymentOrder
from app.models.usage import UsageRecord
from app.services.user_service import UserService
from app.services.translation_service import TranslationService
from app.services.quota_service import QuotaService
from app.services.subscription_service import SubscriptionService
from app.services.payment_service import PaymentService

# Test database setup
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_integration.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    """Override database dependency for testing"""
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

class TestUserServiceIntegration:
    """Test user service integration"""
    
    def setup_method(self):
        """Setup test data"""
        self.db = TestingSessionLocal()
        self.user_service = UserService(self.db)
        
        self.test_user_data = {
            "openid": "test_openid_123",
            "username": "Test User",
            "avatar_url": "https://example.com/avatar.jpg",
            "subscription_level": "free"
        }
    
    def teardown_method(self):
        """Cleanup test data"""
        self.db.close()
    
    def test_user_creation_and_retrieval(self):
        """Test user creation and retrieval integration"""
        # Create user
        user = self.user_service.create_user(self.test_user_data)
        assert user is not None
        assert user.openid == self.test_user_data["openid"]
        
        # Retrieve user
        retrieved_user = self.user_service.get_user_by_openid(self.test_user_data["openid"])
        assert retrieved_user is not None
        assert retrieved_user.id == user.id
        assert retrieved_user.username == self.test_user_data["username"]
    
    def test_user_quota_update_flow(self):
        """Test user quota update flow"""
        # Create user
        user = self.user_service.create_user(self.test_user_data)
        
        # Update quota
        initial_quota = user.quota_used
        new_quota = initial_quota + 1
        
        updated_user = self.user_service.update_quota_usage(user.id, new_quota)
        assert updated_user.quota_used == new_quota
        
        # Verify quota limit enforcement
        quota_service = QuotaService(self.db)
        has_quota = quota_service.check_user_quota(user.id, 1)
        if user.quota_limit <= new_quota:
            assert not has_quota
        else:
            assert has_quota
    
    def test_user_subscription_flow(self):
        """Test user subscription integration"""
        # Create user
        user = self.user_service.create_user(self.test_user_data)
        
        # Create subscription
        subscription_service = SubscriptionService(self.db)
        subscription_data = {
            "user_id": user.id,
            "plan_type": "basic_vip",
            "status": "active",
            "start_date": datetime.now(),
            "monthly_quota": 100,
            "used_quota": 0
        }
        
        subscription = subscription_service.create_subscription(subscription_data)
        assert subscription is not None
        assert subscription.user_id == user.id
        
        # Update user subscription level
        updated_user = self.user_service.update_subscription_level(
            user.id, 
            "basic_vip", 
            subscription.end_date
        )
        assert updated_user.subscription_level == "basic_vip"

class TestTranslationServiceIntegration:
    """Test translation service integration"""
    
    def setup_method(self):
        """Setup test data"""
        self.db = TestingSessionLocal()
        self.translation_service = TranslationService(self.db)
        self.user_service = UserService(self.db)
        
        # Create test user
        user_data = {
            "openid": "translation_test_openid",
            "username": "Translation Test User",
            "subscription_level": "basic_vip",
            "quota_limit": 100
        }
        self.test_user = self.user_service.create_user(user_data)
        
        self.test_translation_data = {
            "task_id": "test_task_123",
            "user_id": self.test_user.id,
            "original_filename": "test_audio.mp3",
            "file_type": "audio",
            "file_size": 1024000,
            "processing_status": "pending"
        }
    
    def teardown_method(self):
        """Cleanup test data"""
        self.db.close()
    
    @patch('app.services.speech_service.SpeechRecognitionService.transcribe_audio')
    def test_complete_translation_workflow(self, mock_transcribe):
        """Test complete translation workflow"""
        # Mock speech recognition
        mock_transcribe.return_value = {
            "text": "This is a test transcription",
            "confidence": 0.95,
            "word_count": 5
        }
        
        # Create translation task
        translation = self.translation_service.create_translation_task(self.test_translation_data)
        assert translation is not None
        assert translation.status == "pending"
        
        # Start processing
        updated_translation = self.translation_service.start_translation_processing(translation.task_id)
        assert updated_translation.processing_status == "processing"
        assert updated_translation.processing_started_at is not None
        
        # Complete processing
        completed_translation = self.translation_service.complete_translation(
            translation.task_id,
            "This is a test transcription",
            0.95,
            5,
            "alibaba"
        )
        
        assert completed_translation.processing_status == "completed"
        assert completed_translation.transcribed_text == "This is a test transcription"
        assert completed_translation.confidence_score == 0.95
        assert completed_translation.word_count == 5
    
    def test_translation_status_tracking(self):
        """Test translation status tracking"""
        # Create translation task
        translation = self.translation_service.create_translation_task(self.test_translation_data)
        
        # Check initial status
        status = self.translation_service.get_translation_status(translation.task_id)
        assert status["status"] == "pending"
        assert status["progress_percentage"] == 0
        
        # Update status
        self.translation_service.update_translation_progress(
            translation.task_id, 
            "processing", 
            50
        )
        
        # Check updated status
        status = self.translation_service.get_translation_status(translation.task_id)
        assert status["status"] == "processing"
        assert status["progress_percentage"] == 50
    
    def test_translation_error_handling(self):
        """Test translation error handling"""
        # Create translation task
        translation = self.translation_service.create_translation_task(self.test_translation_data)
        
        # Simulate error
        error_message = "Speech recognition failed"
        failed_translation = self.translation_service.fail_translation(
            translation.task_id, 
            error_message
        )
        
        assert failed_translation.processing_status == "failed"
        assert failed_translation.processing_error == error_message
        
        # Verify error status
        status = self.translation_service.get_translation_status(translation.task_id)
        assert status["status"] == "failed"
        assert status["error"] == error_message

class TestPaymentServiceIntegration:
    """Test payment service integration"""
    
    def setup_method(self):
        """Setup test data"""
        self.db = TestingSessionLocal()
        self.payment_service = PaymentService(self.db)
        self.user_service = UserService(self.db)
        self.subscription_service = SubscriptionService(self.db)
        
        # Create test user
        user_data = {
            "openid": "payment_test_openid",
            "username": "Payment Test User",
            "subscription_level": "free"
        }
        self.test_user = self.user_service.create_user(user_data)
    
    def teardown_method(self):
        """Cleanup test data"""
        self.db.close()
    
    @patch('app.services.payment_service.wechat_pay_service.create_order')
    def test_payment_order_creation_and_flow(self, mock_wechat_order):
        """Test payment order creation and flow"""
        # Mock WeChat Pay
        mock_wechat_order.return_value = {
            "order_no": "WX_ORDER_123",
            "prepay_id": "PREPAY_ID_123",
            "code_url": "weixin://wxpay/bizpayurl?pr=XXXXX"
        }
        
        # Create payment order
        order_data = {
            "user_id": self.test_user.id,
            "plan_type": "basic_vip",
            "amount": 29.99,
            "payment_method": "wechat"
        }
        
        order = self.payment_service.create_payment_order(order_data)
        assert order is not None
        assert order.user_id == self.test_user.id
        assert order.amount == 29.99
        assert order.payment_status == "pending"
        
        # Process payment
        processed_order = self.payment_service.process_payment(
            order.order_no, 
            "WX_TRANSACTION_123", 
            "paid"
        )
        
        assert processed_order.payment_status == "paid"
        assert processed_order.transaction_id == "WX_TRANSACTION_123"
        assert processed_order.paid_at is not None
    
    def test_payment_status_updates(self):
        """Test payment status updates"""
        # Create payment order
        order_data = {
            "user_id": self.test_user.id,
            "plan_type": "basic_vip",
            "amount": 29.99,
            "payment_method": "wechat"
        }
        
        order = self.payment_service.create_payment_order(order_data)
        
        # Update to failed status
        failed_order = self.payment_service.update_payment_status(
            order.order_no, 
            "failed", 
            "User cancelled payment"
        )
        
        assert failed_order.payment_status == "failed"
        
        # Check status history
        status_history = self.payment_service.get_payment_status_history(order.order_no)
        assert len(status_history) >= 1
        assert status_history[-1]["status"] == "failed"

class TestQuotaServiceIntegration:
    """Test quota service integration"""
    
    def setup_method(self):
        """Setup test data"""
        self.db = TestingSessionLocal()
        self.quota_service = QuotaService(self.db)
        self.user_service = UserService(self.db)
        
        # Create test users with different quota levels
        self.free_user = self.user_service.create_user({
            "openid": "free_test_openid",
            "username": "Free User",
            "subscription_level": "free",
            "quota_limit": 1
        })
        
        self.vip_user = self.user_service.create_user({
            "openid": "vip_test_openid",
            "username": "VIP User",
            "subscription_level": "basic_vip",
            "quota_limit": 100
        })
    
    def teardown_method(self):
        """Cleanup test data"""
        self.db.close()
    
    def test_quota_enforcement(self):
        """Test quota enforcement"""
        # Test free user quota
        has_quota = self.quota_service.check_user_quota(self.free_user.id, 1)
        assert has_quota == True
        
        # Use quota
        self.quota_service.use_quota(self.free_user.id, 1, "translation")
        
        # Check quota again
        has_quota = self.quota_service.check_user_quota(self.free_user.id, 1)
        assert has_quota == False
        
        # Test VIP user quota
        has_quota = self.quota_service.check_user_quota(self.vip_user.id, 1)
        assert has_quota == True
        
        # Use some quota
        self.quota_service.use_quota(self.vip_user.id, 10, "translation")
        
        # Should still have quota
        has_quota = self.quota_service.check_user_quota(self.vip_user.id, 1)
        assert has_quota == True
    
    def test_quota_reset_mechanism(self):
        """Test quota reset mechanism"""
        # Use all quota for free user
        self.quota_service.use_quota(self.free_user.id, 1, "translation")
        
        # Verify no quota remaining
        user = self.user_service.get_user_by_id(self.free_user.id)
        assert user.quota_used >= user.quota_limit
        
        # Reset quota
        self.quota_service.reset_user_quota(self.free_user.id)
        
        # Verify quota reset
        user = self.user_service.get_user_by_id(self.free_user.id)
        assert user.quota_used == 0
    
    def test_quota_usage_tracking(self):
        """Test quota usage tracking"""
        # Use quota for VIP user
        usage_amount = 5
        usage_record = self.quota_service.use_quota(
            self.vip_user.id, 
            usage_amount, 
            "translation",
            description="Test translation"
        )
        
        assert usage_record is not None
        assert usage_record.user_id == self.vip_user.id
        assert usage_record.amount == usage_amount
        assert usage_record.usage_type == "translation"
        
        # Get usage history
        usage_history = self.quota_service.get_user_usage_history(self.vip_user.id)
        assert len(usage_history) >= 1
        assert usage_history[0].amount == usage_amount

class TestSystemServiceIntegration:
    """Test system-level integration"""
    
    def setup_method(self):
        """Setup test data"""
        self.db = TestingSessionLocal()
    
    def teardown_method(self):
        """Cleanup test data"""
        self.db.close()
    
    def test_database_constraints(self):
        """Test database constraints"""
        # Test unique constraint on openid
        user_service = UserService(self.db)
        
        user_data = {
            "openid": "constraint_test_openid",
            "username": "Test User 1"
        }
        
        user1 = user_service.create_user(user_data)
        assert user1 is not None
        
        # Try to create another user with same openid
        user_data2 = {
            "openid": "constraint_test_openid",  # Same openid
            "username": "Test User 2"
        }
        
        # Should raise an exception or return None
        with pytest.raises(Exception):
            user2 = user_service.create_user(user_data2)
    
    def test_foreign_key_constraints(self):
        """Test foreign key constraints"""
        translation_service = TranslationService(self.db)
        
        # Try to create translation with non-existent user_id
        translation_data = {
            "task_id": "fk_test_task",
            "user_id": 99999,  # Non-existent user ID
            "original_filename": "test.mp3",
            "file_type": "audio",
            "processing_status": "pending"
        }
        
        # Should raise an exception due to foreign key constraint
        with pytest.raises(Exception):
            translation = translation_service.create_translation_task(translation_data)
    
    def test_transaction_rollback(self):
        """Test transaction rollback on errors"""
        user_service = UserService(self.db)
        translation_service = TranslationService(self.db)
        
        # Create user first
        user_data = {
            "openid": "transaction_test_openid",
            "username": "Transaction Test User"
        }
        
        user = user_service.create_user(user_data)
        assert user is not None
        
        # Try to create translation with invalid data
        invalid_translation_data = {
            "task_id": None,  # Invalid: task_id cannot be null
            "user_id": user.id,
            "original_filename": "test.mp3",
            "file_type": "audio",
            "processing_status": "pending"
        }
        
        # Should fail and not affect user data
        initial_user_count = self.db.query(User).count()
        
        try:
            translation = translation_service.create_translation_task(invalid_translation_data)
        except Exception:
            pass  # Expected to fail
        
        # Verify user count is unchanged
        final_user_count = self.db.query(User).count()
        assert initial_user_count == final_user_count

class TestEndToEndScenarios:
    """Test end-to-end scenarios"""
    
    def setup_method(self):
        """Setup test data"""
        self.db = TestingSessionLocal()
        
        # Initialize services
        self.user_service = UserService(self.db)
        self.translation_service = TranslationService(self.db)
        self.quota_service = QuotaService(self.db)
        self.subscription_service = SubscriptionService(self.db)
        self.payment_service = PaymentService(self.db)
    
    def teardown_method(self):
        """Cleanup test data"""
        self.db.close()
    
    @patch('app.services.speech_service.SpeechRecognitionService.transcribe_audio')
    @patch('app.services.payment_service.wechat_pay_service.create_order')
    def test_complete_user_journey(self, mock_wechat_order, mock_transcribe):
        """Test complete user journey from signup to translation"""
        # Mock external services
        mock_transcribe.return_value = {
            "text": "Complete journey test transcription",
            "confidence": 0.98,
            "word_count": 4
        }
        
        mock_wechat_order.return_value = {
            "order_no": "WX_JOURNEY_123",
            "prepay_id": "PREPAY_JOURNEY_123"
        }
        
        # Step 1: User signup
        user_data = {
            "openid": "journey_test_openid",
            "username": "Journey Test User",
            "subscription_level": "free",
            "quota_limit": 1
        }
        
        user = self.user_service.create_user(user_data)
        assert user is not None
        
        # Step 2: Check initial quota
        quota_status = self.quota_service.get_user_quota_status(user.id)
        assert quota_status["quota_remaining"] == 1
        
        # Step 3: Create translation task
        translation_data = {
            "task_id": "journey_task_123",
            "user_id": user.id,
            "original_filename": "journey_test.mp3",
            "file_type": "audio",
            "processing_status": "pending"
        }
        
        translation = self.translation_service.create_translation_task(translation_data)
        assert translation is not None
        
        # Step 4: Use quota for translation
        quota_used = self.quota_service.use_quota(user.id, 1, "translation")
        assert quota_used is not None
        
        # Step 5: Process translation
        self.translation_service.start_translation_processing(translation.task_id)
        
        completed_translation = self.translation_service.complete_translation(
            translation.task_id,
            "Complete journey test transcription",
            0.98,
            4,
            "alibaba"
        )
        
        assert completed_translation.processing_status == "completed"
        
        # Step 6: Check quota after translation
        quota_status = self.quota_service.get_user_quota_status(user.id)
        assert quota_status["quota_remaining"] == 0
        
        # Step 7: Upgrade subscription
        subscription_data = {
            "user_id": user.id,
            "plan_type": "basic_vip",
            "status": "active",
            "start_date": datetime.now(),
            "monthly_quota": 100,
            "used_quota": 0
        }
        
        subscription = self.subscription_service.create_subscription(subscription_data)
        assert subscription is not None
        
        # Step 8: Update user subscription
        updated_user = self.user_service.update_subscription_level(
            user.id,
            "basic_vip",
            subscription.end_date
        )
        assert updated_user.subscription_level == "basic_vip"
        
        # Step 9: Reset quota for new subscription
        self.quota_service.reset_user_quota(user.id)
        
        # Step 10: Verify new quota
        quota_status = self.quota_service.get_user_quota_status(user.id)
        assert quota_status["quota_remaining"] == 100
        
        # Journey completed successfully
        assert True

if __name__ == "__main__":
    pytest.main([__file__, "-v"])