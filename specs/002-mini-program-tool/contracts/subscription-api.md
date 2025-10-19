# Subscription API Contract

**Version**: 1.0  
**Purpose**: VIP subscription plans, payments, and quota management APIs

## Endpoints

### 1. Get Subscription Plans

**Endpoint**: `GET /api/v1/subscription/plans`  
**Authentication**: None required  

#### Response (200 OK)

```json
{
  "success": true,
  "data": [
    {
      "id": 1,
      "name": "基础VIP",
      "code": "basic_vip",
      "price": 29.00,
      "billingCycle": "monthly",
      "quotaLimit": 50,
      "features": [
        "每月50次翻译",
        "支持所有文件格式",
        "优先处理队列",
        "邮件客服支持"
      ],
      "isPopular": false,
      "description": "适合轻度使用用户"
    },
    {
      "id": 2,
      "name": "高级VIP",
      "code": "premium_vip",
      "price": 99.00,
      "billingCycle": "monthly",
      "quotaLimit": 200,
      "features": [
        "每月200次翻译",
        "支持所有文件格式",
        "最高优先级处理",
        "24小时客服支持",
        "API访问权限",
        "自定义模型选择"
      ],
      "isPopular": true,
      "description": "适合重度使用用户"
    }
  ]
}
```

### 2. Create Subscription Order

**Endpoint**: `POST /api/v1/subscription/orders`  
**Authentication**: Valid JWT token required  

#### Request

```json
{
  "planId": 2,
  "billingCycle": "monthly",  // "monthly" | "yearly"
  "paymentMethod": "wechat_pay"
}
```

#### Response (200 OK)

```json
{
  "success": true,
  "data": {
    "orderId": "order_1234567890",
    "orderNo": "202411151234567890",
    "plan": {
      "id": 2,
      "name": "高级VIP",
      "code": "premium_vip"
    },
    "amount": 99.00,
    "currency": "CNY",
    "billingCycle": "monthly",
    "expiresAt": "2024-11-15T10:45:00Z"
  }
}
```

### 3. Initiate WeChat Payment

**Endpoint**: `POST /api/v1/subscription/pay/wechat`  
**Authentication**: Valid JWT token required  

#### Request

```json
{
  "orderId": "order_1234567890"
}
```

#### Response (200 OK)

```json
{
  "success": true,
  "data": {
    "paymentParams": {
      "appId": "wx123...",
      "timeStamp": "1642234567",
      "nonceStr": "random_string",
      "package": "prepay_id=wx151030123456789abcdef123456789",
      "signType": "RSA",
      "paySign": "signature_string"
    },
    "prepayId": "wx151030123456789abcdef123456789"
  }
}
```

### 4. Get User Subscription

**Endpoint**: `GET /api/v1/subscription/current`  
**Authentication**: Valid JWT token required  

#### Response (200 OK)

```json
{
  "success": true,
  "data": {
    "id": 2,
    "name": "高级VIP",
    "code": "premium_vip",
    "status": "active",  // "active" | "expired" | "cancelled"
    "quotaLimit": 200,
    "quotaUsed": 15,
    "quotaRemaining": 185,
    "quotaResetDate": "2024-12-01",
    "currentPeriodStart": "2024-11-01T00:00:00Z",
    "currentPeriodEnd": "2024-12-01T00:00:00Z",
    "cancelledAt": null,
    "autoRenew": true,
    "nextBillingDate": "2024-12-01T00:00:00Z"
  }
}
```

### 5. Update Subscription

**Endpoint**: `PUT /api/v1/subscription/manage`  
**Authentication**: Valid JWT token required  

#### Request

```json
{
  "action": "cancel",        // "cancel" | "resume" | "upgrade" | "downgrade"
  "planId": 1,              // Required for upgrade/downgrade
  "reason": "string"        // Optional: reason for cancellation
}
```

#### Response (200 OK)

```json
{
  "success": true,
  "data": {
    "id": 2,
    "status": "cancelled",
    "cancelledAt": "2024-11-15T10:30:00Z",
    "currentPeriodEnd": "2024-12-01T00:00:00Z",
    "message": "订阅已取消，将在当前计费周期结束后停止服务"
  }
}
```

### 6. Payment Callback (Webhook)

**Endpoint**: `POST /api/v1/subscription/webhook/wechat`  
**Authentication**: WeChat signature verification  
**Purpose**: Receive payment notifications from WeChat Pay

#### Request (WeChat Pay format)

```json
{
  "id": "ev-202411151234567890",
  "create_time": "2024-11-15T10:30:00+08:00",
  "resource_type": "encrypt-resource",
  "event_type": "TRANSACTION.SUCCESS",
  "resource": {
    "original_type": "transaction",
    "algorithm": "AEAD_AES_256_GCM",
    "ciphertext": "encrypted_data",
    "associated_data": "transaction",
    "nonce": "nonce_string"
  }
}
```

#### Response (200 OK)

```json
{
  "code": "SUCCESS",
  "message": "success"
}
```