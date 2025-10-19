# User Management API Contract

**Version**: 1.0  
**Purpose**: User profile, preferences, and account management APIs

## Endpoints

### 1. Update User Profile

**Endpoint**: `PUT /api/v1/users/profile`  
**Authentication**: Valid JWT token required  

#### Request

```json
{
  "username": "string",
  "avatarUrl": "string",
  "phone": "string",
  "email": "string"
}
```

#### Response (200 OK)

```json
{
  "success": true,
  "data": {
    "id": 123,
    "openid": "wx123...",
    "username": "张三",
    "avatarUrl": "https://...",
    "phone": "138****5678",
    "email": "user@example.com",
    "subscriptionLevel": "basic_vip",
    "quotaUsed": 5,
    "quotaLimit": 10,
    "updatedAt": "2024-11-15T10:30:00Z"
  }
}
```

### 2. Get User Statistics

**Endpoint**: `GET /api/v1/users/stats`  
**Authentication**: Valid JWT token required  

#### Response (200 OK)

```json
{
  "success": true,
  "data": {
    "totalTranslations": 45,
    "totalDuration": 3600.5,
    "averageConfidence": 0.95,
    "quotaUsed": 5,
    "quotaRemaining": 5,
    "quotaResetDate": "2024-12-01",
    "subscriptionExpiresAt": "2024-12-31T23:59:59Z",
    "monthlyUsage": [
      {
        "month": "2024-11",
        "translations": 15,
        "duration": 1200.5
      }
    ]
  }
}
```

### 3. Delete User Account

**Endpoint**: `DELETE /api/v1/users/account`  
**Authentication**: Valid JWT token required  

#### Request

```json
{
  "password": "string",  // Required for account deletion
  "reason": "string"     // Optional deletion reason
}
```

#### Response (200 OK)

```json
{
  "success": true,
  "message": "账户已成功删除"
}
```