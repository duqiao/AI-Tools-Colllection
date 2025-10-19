"""
Payment service for handling payment processing with WeChat Pay and Alipay.

This module provides integration with payment providers for subscription purchases.
"""

from typing import Optional, Dict, Any
import hashlib
import time
import json
from decimal import Decimal

from app.models.subscription import PaymentOrder
from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class PaymentService:
    """Service for payment processing operations."""
    
    def __init__(self, db):
        self.db = db
    
    def create_wechat_payment(
        self,
        order_no: str,
        amount: Decimal,
        description: str,
        openid: str
    ) -> Dict[str, Any]:
        """Create WeChat Pay payment parameters."""
        
        # WeChat Pay API parameters (mock implementation)
        payment_params = {
            "appId": settings.wechat_appid,
            "timeStamp": str(int(time.time())),
            "nonceStr": self._generate_nonce_str(),
            "package": f"prepay_id={self._generate_prepay_id(order_no)}",
            "signType": "MD5"
        }
        
        # Generate signature
        payment_params["paySign"] = self._generate_wechat_sign(payment_params)
        
        logger.info(f"Created WeChat payment for order: {order_no}")
        return {
            "success": True,
            "payment_params": payment_params,
            "order_no": order_no
        }
    
    def create_alipay_payment(
        self,
        order_no: str,
        amount: Decimal,
        description: str,
        return_url: str = None
    ) -> Dict[str, Any]:
        """Create Alipay payment parameters."""
        
        # Alipay API parameters (mock implementation)
        payment_params = {
            "app_id": settings.alipay_appid,
            "method": "alipay.trade.app.pay",
            "charset": "utf-8",
            "sign_type": "RSA2",
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "version": "1.0",
            "notify_url": f"{settings.base_url}/api/v1/payment/alipay/notify",
            "biz_content": json.dumps({
                "out_trade_no": order_no,
                "total_amount": str(amount),
                "subject": description,
                "product_code": "QUICK_MSECURITY_PAY"
            })
        }
        
        # Generate signature
        payment_params["sign"] = self._generate_alipay_sign(payment_params)
        
        logger.info(f"Created Alipay payment for order: {order_no}")
        return {
            "success": True,
            "payment_params": payment_params,
            "order_no": order_no
        }
    
    def verify_wechat_payment(self, payment_data: Dict[str, Any]) -> bool:
        """Verify WeChat payment callback."""
        # In production, verify signature with WeChat Pay public key
        # This is a mock implementation
        transaction_id = payment_data.get("transaction_id")
        out_trade_no = payment_data.get("out_trade_no")
        result_code = payment_data.get("result_code")
        
        if result_code != "SUCCESS":
            logger.error(f"WeChat payment failed: {payment_data}")
            return False
        
        # Update payment order status
        order = self.db.query(PaymentOrder).filter(
            PaymentOrder.order_no == out_trade_no
        ).first()
        
        if not order:
            logger.error(f"Order not found for WeChat payment: {out_trade_no}")
            return False
        
        if order.is_paid:
            logger.warning(f"Order already paid: {out_trade_no}")
            return True
        
        order.payment_status = "paid"
        order.transaction_id = transaction_id
        order.paid_at = datetime.utcnow()
        
        self.db.commit()
        
        logger.info(f"WeChat payment verified for order: {out_trade_no}")
        return True
    
    def verify_alipay_payment(self, payment_data: Dict[str, Any]) -> bool:
        """Verify Alipay payment callback."""
        # In production, verify signature with Alipay public key
        # This is a mock implementation
        trade_status = payment_data.get("trade_status")
        out_trade_no = payment_data.get("out_trade_no")
        trade_no = payment_data.get("trade_no")
        
        if trade_status != "TRADE_SUCCESS":
            logger.error(f"Alipay payment failed: {payment_data}")
            return False
        
        # Update payment order status
        order = self.db.query(PaymentOrder).filter(
            PaymentOrder.order_no == out_trade_no
        ).first()
        
        if not order:
            logger.error(f"Order not found for Alipay payment: {out_trade_no}")
            return False
        
        if order.is_paid:
            logger.warning(f"Order already paid: {out_trade_no}")
            return True
        
        order.payment_status = "paid"
        order.transaction_id = trade_no
        order.paid_at = datetime.utcnow()
        
        self.db.commit()
        
        logger.info(f"Alipay payment verified for order: {out_trade_no}")
        return True
    
    def query_payment_status(self, order_no: str, payment_method: str) -> Dict[str, Any]:
        """Query payment status from provider."""
        order = self.db.query(PaymentOrder).filter(
            PaymentOrder.order_no == order_no
        ).first()
        
        if not order:
            return {
                "success": False,
                "error": "Order not found"
            }
        
        # In production, query actual payment provider API
        # This is a mock implementation
        return {
            "success": True,
            "order_no": order_no,
            "payment_status": order.payment_status,
            "transaction_id": order.transaction_id,
            "paid_at": order.paid_at.isoformat() if order.paid_at else None
        }
    
    def refund_payment(
        self,
        order_no: str,
        refund_amount: Optional[Decimal] = None,
        reason: str = "User requested refund"
    ) -> Dict[str, Any]:
        """Process payment refund."""
        order = self.db.query(PaymentOrder).filter(
            PaymentOrder.order_no == order_no
        ).first()
        
        if not order or not order.is_paid:
            return {
                "success": False,
                "error": "Order not found or not paid"
            }
        
        if refund_amount is None:
            refund_amount = order.amount
        
        # In production, call actual refund API
        # This is a mock implementation
        refund_id = f"RF{order_no}{int(time.time())}"
        
        logger.info(f"Processed refund for order: {order_no}, amount: {refund_amount}")
        
        return {
            "success": True,
            "refund_id": refund_id,
            "refund_amount": str(refund_amount),
            "reason": reason
        }
    
    def _generate_nonce_str(self, length: int = 32) -> str:
        """Generate random nonce string."""
        import random
        import string
        
        chars = string.ascii_letters + string.digits
        return ''.join(random.choice(chars) for _ in range(length))
    
    def _generate_prepay_id(self, order_no: str) -> str:
        """Generate mock prepay ID."""
        return f"wx{int(time.time())}{hash(order_no) % 10000:04d}"
    
    def _generate_wechat_sign(self, params: Dict[str, Any]) -> str:
        """Generate WeChat Pay signature (mock implementation)."""
        # In production, use actual WeChat Pay key and MD5 algorithm
        sorted_params = sorted(params.items())
        sign_string = '&'.join([f"{k}={v}" for k, v in sorted_params])
        sign_string += f"&key={settings.wechat_pay_key}"
        
        return hashlib.md5(sign_string.encode('utf-8')).hexdigest().upper()
    
    def _generate_alipay_sign(self, params: Dict[str, Any]) -> str:
        """Generate Alipay signature (mock implementation)."""
        # In production, use actual Alipay private key and RSA algorithm
        sorted_params = sorted(params.items())
        sign_string = '&'.join([f"{k}={v}" for k, v in sorted_params])
        
        # Mock signature - in production use RSA private key
        return hashlib.md5(sign_string.encode('utf-8')).hexdigest()