# Authentication API Contract

**Version**: 1.0  
**Purpose**: User authentication and session management for uni-app and FastAPI integration

## Overview

Authentication APIs handle user login via WeChat, session management, and token-based authorization for all protected endpoints.

## Endpoints

### 1. WeChat Login

**Endpoint**: `POST /api/v1/auth/wechat-login`  
**Description**: Authenticate user using WeChat authorization code  
**Authentication**: None required  

#### Request

```json
{
  "code": "string",           // WeChat authorization code
  "userInfo": {               // Optional: User profile info
    "nickname": "string",
    "avatarUrl": "string",
    "gender": 1,              // 0=unknown, 1=male, 2=female
    "language": "zh_CN",
    "city": "string",
    "province": "string", 
    "country": "string"
  }
}
```

#### Response (200 OK)

```json
{
  "success": true,
  "data": {
    "user": {
      "id": 123,
      "openid": "wx123...",
      "username": "张三",
      "avatarUrl": "https://...",
      "subscriptionLevel": "basic_vip",
      "quotaUsed": 5,
      "quotaLimit": 10,
      "quotaResetDate": "2024-12-01"
    },
    "token": "eyJhbGciOiJIUzI1NiIs...",  // JWT token
    "expiresIn": 86400,                  // Token expiration in seconds
    "isNewUser": false                   // Whether this is a new user registration
  },
  "message": "登录成功"
}
```

#### Error Responses

```json
// 400 Bad Request - Invalid code
{
  "success": false,
  "error": {
    "code": "INVALID_CODE",
    "message": "无效的授权码"
  }
}

// 429 Too Many Requests
{
  "success": false,
  "error": {
    "code": "RATE_LIMIT_EXCEEDED",
    "message": "请求过于频繁，请稍后再试"
  }
}
```

### 2. Refresh Token

**Endpoint**: `POST /api/v1/auth/refresh`  
**Description**: Refresh JWT token using existing token  
**Authentication**: Valid JWT token required  

#### Request

```json
{
  "token": "eyJhbGciOiJIUzI1NiIs..."
}
```

#### Response (200 OK)

```json
{
  "success": true,
  "data": {
    "token": "eyJhbGciOiJIUzI1NiIs...",  // New JWT token
    "expiresIn": 86400
  },
  "message": "令牌刷新成功"
}
```

### 3. Logout

**Endpoint**: `POST /api/v1/auth/logout`  
**Description**: Invalidate current session and token  
**Authentication**: Valid JWT token required  

#### Request

```json
{
  "token": "eyJhbGciOiJIUzI1NiIs..."
}
```

#### Response (200 OK)

```json
{
  "success": true,
  "message": "退出登录成功"
}
```

### 4. Get Current User Info

**Endpoint**: `GET /api/v1/auth/me`  
**Description**: Get current user information  
**Authentication**: Valid JWT token required  

#### Response (200 OK)

```json
{
  "success": true,
  "data": {
    "id": 123,
    "openid": "wx123...",
    "username": "张三",
    "avatarUrl": "https://...",
    "subscriptionLevel": "basic_vip",
    "quotaUsed": 5,
    "quotaLimit": 10,
    "quotaResetDate": "2024-12-01",
    "subscriptionExpiresAt": "2024-12-31T23:59:59Z",
    "isActive": true,
    "lastLoginAt": "2024-11-15T10:30:00Z",
    "createdAt": "2024-11-01T08:00:00Z"
  }
}
```

## Data Models

### User

```typescript
interface User {
  id: number;
  openid: string;
  username?: string;
  avatarUrl?: string;
  subscriptionLevel: 'free' | 'basic_vip' | 'premium_vip';
  quotaUsed: number;
  quotaLimit: number;
  quotaResetDate?: string;  // YYYY-MM-DD format
  subscriptionExpiresAt?: string;  // ISO 8601 format
  isActive: boolean;
  lastLoginAt?: string;  // ISO 8601 format
  createdAt: string;  // ISO 8601 format
}
```

### WeChatUserInfo

```typescript
interface WeChatUserInfo {
  nickname?: string;
  avatarUrl?: string;
  gender?: 0 | 1 | 2;  // 0=unknown, 1=male, 2=female
  language?: string;
  city?: string;
  province?: string;
  country?: string;
}
```

### AuthResponse

```typescript
interface AuthResponse {
  user: User;
  token: string;
  expiresIn: number;
  isNewUser: boolean;
}
```

## Authentication Flow

### 1. Initial Login (uni-app)

```typescript
// uni-app WeChat login
uni.login({
  provider: 'weixin',
  success: async (loginRes) => {
    try {
      // Get user info (optional)
      const userInfo = await uni.getUserInfo();
      
      // Send to backend
      const response = await api.post('/auth/wechat-login', {
        code: loginRes.code,
        userInfo: userInfo.userInfo
      });
      
      // Store token and user info
      uni.setStorageSync('token', response.data.token);
      store.setUser(response.data.user);
      
    } catch (error) {
      console.error('Login failed:', error);
    }
  }
});
```

### 2. Token Management (uni-app)

```typescript
// Request interceptor for API calls
const request = async (url: string, options: RequestOptions = {}) => {
  const token = uni.getStorageSync('token');
  
  if (token) {
    options.header = {
      ...options.header,
      'Authorization': `Bearer ${token}`
    };
  }
  
  return uni.request({
    url: `${API_BASE_URL}${url}`,
    ...options
  });
};

// Auto-refresh token
const refreshToken = async () => {
  try {
    const response = await request('/auth/refresh', {
      method: 'POST',
      data: { token: uni.getStorageSync('token') }
    });
    
    uni.setStorageSync('token', response.data.token);
  } catch (error) {
    // Refresh failed, redirect to login
    uni.removeStorageSync('token');
    uni.navigateTo({ url: '/pages/login/login' });
  }
};
```

## Security Considerations

### 1. Token Security

- **JWT Secret**: Use strong, randomly generated secret
- **Token Expiration**: 24-hour token expiration with refresh capability
- **Token Storage**: Store in uni-app secure storage
- **HTTPS Only**: All API calls must use HTTPS

### 2. WeChat Integration

- **Code Validation**: Validate WeChat authorization codes
- **OpenID Verification**: Verify user identity through OpenID
- **Session Management**: Secure session handling on backend

### 3. Rate Limiting

- **Login Attempts**: Limit login attempts per IP/user
- **Token Refresh**: Limit refresh token requests
- **API Calls**: General rate limiting for authenticated endpoints

## Error Handling

### Error Response Format

```typescript
interface ErrorResponse {
  success: false;
  error: {
    code: string;
    message: string;
    details?: any;
  };
}
```

### Common Error Codes

| Error Code | HTTP Status | Description |
|------------|-------------|-------------|
| `INVALID_CODE` | 400 | Invalid WeChat authorization code |
| `TOKEN_EXPIRED` | 401 | JWT token has expired |
| `TOKEN_INVALID` | 401 | JWT token is invalid |
| `USER_NOT_FOUND` | 404 | User not found |
| `RATE_LIMIT_EXCEEDED` | 429 | Too many requests |
| `INTERNAL_ERROR` | 500 | Internal server error |

## Testing

### Unit Tests

```python
# FastAPI test example
async def test_wechat_login_success(client):
    response = await client.post("/api/v1/auth/wechat-login", json={
        "code": "valid_wechat_code",
        "userInfo": {
            "nickname": "测试用户",
            "avatarUrl": "https://example.com/avatar.jpg"
        }
    })
    
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "token" in data["data"]
    assert "user" in data["data"]
```

### Integration Tests

```typescript
// uni-app integration test
describe('Authentication Flow', () => {
  it('should login with WeChat and store token', async () => {
    // Mock WeChat login
    const mockLoginRes = { code: 'test_code' };
    jest.spyOn(uni, 'login').mockImplementation(({ success }) => {
      success(mockLoginRes);
    });
    
    // Perform login
    const result = await authService.loginByWechat();
    
    // Verify token stored
    expect(uni.setStorageSync).toHaveBeenCalledWith('token', expect.any(String));
    expect(result.user).toBeDefined();
  });
});
```

## Migration Notes

### From Node.js to FastAPI

1. **Route Structure**: Maintain identical URL patterns
2. **Response Format**: Preserve JSON response structure
3. **Error Handling**: Keep error codes and messages consistent
4. **Authentication Flow**: No changes to client-side logic

### Compatibility Requirements

- **URL Paths**: All endpoint paths must remain identical
- **HTTP Methods**: No changes to HTTP verb usage
- **Request Format**: JSON request structure must be preserved
- **Response Format**: Response JSON structure must be identical
- **Status Codes**: HTTP status codes must remain consistent