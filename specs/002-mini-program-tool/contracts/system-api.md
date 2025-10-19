# System API Contract

**Version**: 1.0  
**Purpose**: System configuration, settings, and administrative APIs

## Endpoints

### 1. Get System Configuration

**Endpoint**: `GET /api/v1/system/config`  
**Authentication**: None required (public settings)

#### Response (200 OK)

```json
{
  "success": true,
  "data": {
    "app": {
      "name": "媒体翻译器",
      "version": "1.0.0",
      "minVersion": "1.0.0",
      "updateUrl": "https://example.com/update"
    },
    "features": {
      "maxFileSize": 104857600,  // 100MB in bytes
      "supportedFormats": ["mp3", "wav", "mp4", "mov", "avi"],
      "freeQuotaLimit": 1,
      "maxConcurrentTasks": 3
    },
    "pricing": {
      "currency": "CNY",
      "plans": [
        {
          "code": "basic_vip",
          "price": 29.00,
          "quotaLimit": 50
        },
        {
          "code": "premium_vip", 
          "price": 99.00,
          "quotaLimit": 200
        }
      ]
    },
    "limits": {
      "uploadTimeout": 300,      // 5 minutes
      "translationTimeout": 1800, // 30 minutes
      "apiRateLimit": 100         // requests per minute
    }
  }
}
```

### 2. Health Check

**Endpoint**: `GET /api/v1/system/health`  
**Authentication**: None required  

#### Response (200 OK)

```json
{
  "success": true,
  "data": {
    "status": "healthy",
    "timestamp": "2024-11-15T10:30:00Z",
    "version": "1.0.0",
    "uptime": 86400,  // seconds
    "services": {
      "database": "healthy",
      "redis": "healthy",
      "fileStorage": "healthy",
      "speechRecognition": "healthy"
    },
    "performance": {
      "cpuUsage": 25.5,
      "memoryUsage": 60.2,
      "diskUsage": 45.8
    }
  }
}
```

### 3. Get App Changelog

**Endpoint**: `GET /api/v1/system/changelog`  
**Authentication**: None required  

#### Response (200 OK)

```json
{
  "success": true,
  "data": [
    {
      "version": "1.0.0",
      "releaseDate": "2024-11-15",
      "changes": [
        {
          "type": "feature",
          "description": "新增语音转文字功能"
        },
        {
          "type": "improvement", 
          "description": "优化翻译准确度"
        },
        {
          "type": "bugfix",
          "description": "修复文件上传失败问题"
        }
      ]
    }
  ]
}
```

### 4. Report Issue/Bug

**Endpoint**: `POST /api/v1/system/feedback`  
**Authentication**: Valid JWT token required  

#### Request

```json
{
  "type": "bug",  // "bug" | "suggestion" | "other"
  "title": "string",
  "description": "string",
  "taskId": "task_123456789",  // Optional: related task ID
  "deviceInfo": {
    "platform": "ios",
    "version": "17.1",
    "appVersion": "1.0.0"
  },
  "attachments": ["https://cdn.example.com/screenshots/1.jpg"]
}
```

#### Response (200 OK)

```json
{
  "success": true,
  "data": {
    "feedbackId": "fb_123456789",
    "status": "received",
    "submittedAt": "2024-11-15T10:30:00Z"
  },
  "message": "感谢您的反馈，我们会尽快处理"
}
```

## Error Response Format

### Standard Error Structure

```json
{
  "success": false,
  "error": {
    "code": "ERROR_CODE",
    "message": "错误描述",
    "details": {
      "field": "具体错误信息"
    }
  },
  "timestamp": "2024-11-15T10:30:00Z"
}
```

### Common System Error Codes

| Error Code | HTTP Status | Description |
|------------|-------------|-------------|
| `MAINTENANCE_MODE` | 503 | System under maintenance |
| `RATE_LIMIT_EXCEEDED` | 429 | API rate limit exceeded |
| `SERVICE_UNAVAILABLE` | 503 | External service unavailable |
| `INVALID_REQUEST` | 400 | Invalid request format |
| `INTERNAL_ERROR` | 500 | Internal server error |