# Translation API Contract

**Version**: 1.0  
**Purpose**: Media file processing and transcription APIs for uni-app and FastAPI integration

## Overview

Translation APIs handle media file uploads, transcription processing, status tracking, and result retrieval for voice, video, audio, and link-based content.

## Endpoints

### 1. Upload Media File

**Endpoint**: `POST /api/v1/translation/upload`  
**Description**: Upload media file for transcription processing  
**Authentication**: Valid JWT token required  
**Content-Type**: `multipart/form-data`

#### Request

```
POST /api/v1/translation/upload
Authorization: Bearer <token>
Content-Type: multipart/form-data

file: <binary_file_data>
type: "audio" | "video" | "wechat_video" | "link"
linkUrl: "https://example.com/media.mp4"  // Required only if type="link"
```

#### Response (200 OK)

```json
{
  "success": true,
  "data": {
    "uploadId": "upload_123456789",
    "filename": "audio.mp3",
    "fileSize": 1048576,  // File size in bytes
    "fileType": "audio",
    "mimeType": "audio/mpeg",
    "duration": 120.5,    // Duration in seconds (for audio/video)
    "uploadUrl": "https://cdn.example.com/uploads/audio_123456789.mp3",
    "expiresAt": "2024-11-16T10:30:00Z"  // Upload URL expiration
  },
  "message": "文件上传成功"
}
```

#### Error Responses

```json
// 400 Bad Request - Invalid file type
{
  "success": false,
  "error": {
    "code": "INVALID_FILE_TYPE",
    "message": "不支持的文件类型"
  }
}

// 413 Payload Too Large
{
  "success": false,
  "error": {
    "code": "FILE_TOO_LARGE",
    "message": "文件大小超过限制 (最大 100MB)"
  }
}

// 402 Payment Required - Quota exceeded
{
  "success": false,
  "error": {
    "code": "QUOTA_EXCEEDED",
    "message": "翻译次数已用完，请升级VIP套餐",
    "data": {
      "quotaUsed": 1,
      "quotaLimit": 1,
      "upgradeUrl": "/pages/subscription/subscription"
    }
  }
}
```

### 2. Start Translation

**Endpoint**: `POST /api/v1/translation/start`  
**Description**: Start transcription processing for uploaded media  
**Authentication**: Valid JWT token required  

#### Request

```json
{
  "uploadId": "upload_123456789",
  "options": {
    "language": "zh-CN",           // Target language for transcription
    "quality": "standard",         // "standard" | "high" 
    "speakerDiarization": false,   // Whether to identify different speakers
    "punctuation": true,           // Whether to add punctuation
    "timestamps": false            // Whether to include timestamps
  }
}
```

#### Response (200 OK)

```json
{
  "success": true,
  "data": {
    "taskId": "task_123456789_abcdef",
    "status": "processing",        // "pending" | "processing" | "completed" | "failed"
    "estimatedDuration": 180,      // Estimated processing time in seconds
    "queuePosition": 3,            // Position in processing queue
    "createdAt": "2024-11-15T10:30:00Z"
  },
  "message": "翻译任务已开始"
}
```

### 3. Get Translation Status

**Endpoint**: `GET /api/v1/translation/{taskId}/status`  
**Description**: Get current processing status and progress  
**Authentication**: Valid JWT token required  

#### Response (200 OK)

```json
{
  "success": true,
  "data": {
    "taskId": "task_123456789_abcdef",
    "status": "processing",
    "progress": 65,               // Progress percentage (0-100)
    "currentStep": "transcribing", // "uploading" | "queued" | "transcribing" | "finalizing"
    "estimatedTimeRemaining": 63,  // Seconds remaining
    "startedAt": "2024-11-15T10:30:00Z",
    "updatedAt": "2024-11-15T10:31:05Z"
  }
}
```

#### Response for Completed Task

```json
{
  "success": true,
  "data": {
    "taskId": "task_123456789_abcdef",
    "status": "completed",
    "progress": 100,
    "result": {
      "text": "转录的文本内容...",
      "confidence": 0.95,         // Overall confidence score (0-1)
      "wordCount": 156,
      "duration": 120.5,
      "language": "zh-CN",
      "segments": [               // Text segments with timestamps
        {
          "text": "第一段文本",
          "startTime": 0.0,
          "endTime": 5.2,
          "confidence": 0.98
        }
      ]
    },
    "completedAt": "2024-11-15T10:33:00Z"
  }
}
```

### 4. Get Translation Result

**Endpoint**: `GET /api/v1/translation/{taskId}/result`  
**Description**: Get final transcription result and metadata  
**Authentication**: Valid JWT token required  

#### Response (200 OK)

```json
{
  "success": true,
  "data": {
    "taskId": "task_123456789_abcdef",
    "originalFile": {
      "filename": "audio.mp3",
      "fileType": "audio",
      "fileSize": 1048576,
      "duration": 120.5,
      "url": "https://cdn.example.com/uploads/audio_123456789.mp3"
    },
    "transcription": {
      "text": "转录的文本内容...",
      "confidence": 0.95,
      "wordCount": 156,
      "language": "zh-CN",
      "processingTime": 180,      // Total processing time in seconds
      "segments": [
        {
          "text": "第一段文本",
          "startTime": 0.0,
          "endTime": 5.2,
          "confidence": 0.98,
          "speaker": 1             // Speaker ID if diarization enabled
        }
      ]
    },
    "metadata": {
      "serviceProvider": "alibaba_cloud",
      "model": "paraformer-v1",
      "cost": 0.0250,            // Service cost in CNY
      "quotaUsed": 1,
      "createdAt": "2024-11-15T10:30:00Z",
      "completedAt": "2024-11-15T10:33:00Z"
    }
  }
}
```

### 5. Get Translation History

**Endpoint**: `GET /api/v1/translation/history`  
**Description**: Get user's translation history with pagination  
**Authentication**: Valid JWT token required  

#### Query Parameters

```
page: number = 1          // Page number (default: 1)
limit: number = 20        // Items per page (default: 20, max: 100)
status?: string           // Filter by status: "completed" | "failed" | "all"
fileType?: string         // Filter by file type: "audio" | "video" | "wechat_video" | "link"
startDate?: string        // Filter by start date (YYYY-MM-DD)
endDate?: string          // Filter by end date (YYYY-MM-DD)
```

#### Response (200 OK)

```json
{
  "success": true,
  "data": {
    "translations": [
      {
        "taskId": "task_123456789_abcdef",
        "originalFilename": "audio.mp3",
        "fileType": "audio",
        "duration": 120.5,
        "status": "completed",
        "text": "转录的文本内容...",
        "confidence": 0.95,
        "wordCount": 156,
        "createdAt": "2024-11-15T10:30:00Z",
        "completedAt": "2024-11-15T10:33:00Z"
      }
    ],
    "pagination": {
      "page": 1,
      "limit": 20,
      "total": 45,
      "totalPages": 3,
      "hasNext": true,
      "hasPrev": false
    }
  }
}
```

### 6. Delete Translation

**Endpoint**: `DELETE /api/v1/translation/{taskId}`  
**Description**: Delete translation record and associated files  
**Authentication**: Valid JWT token required  

#### Response (200 OK)

```json
{
  "success": true,
  "message": "翻译记录已删除"
}
```

## Data Models

### TranslationTask

```typescript
interface TranslationTask {
  taskId: string;
  userId: number;
  originalFile: {
    filename: string;
    fileType: 'audio' | 'video' | 'wechat_video' | 'link';
    fileSize: number;
    mimeType: string;
    duration?: number;        // For audio/video files
    url?: string;            // CDN URL
  };
  status: 'pending' | 'processing' | 'completed' | 'failed';
  progress: number;          // 0-100
  currentStep?: string;
  transcription?: {
    text: string;
    confidence: number;      // 0-1
    wordCount: number;
    language: string;
    segments?: TranscriptionSegment[];
  };
  metadata: {
    serviceProvider: string;
    model: string;
    cost: number;
    quotaUsed: number;
    processingTime: number;
    createdAt: string;
    completedAt?: string;
    failedAt?: string;
    error?: string;
  };
}

interface TranscriptionSegment {
  text: string;
  startTime: number;
  endTime: number;
  confidence: number;
  speaker?: number;          // Speaker ID if diarization enabled
}
```

### UploadResponse

```typescript
interface UploadResponse {
  uploadId: string;
  filename: string;
  fileSize: number;
  fileType: string;
  mimeType: string;
  duration?: number;
  uploadUrl: string;
  expiresAt: string;
}
```

### TranslationOptions

```typescript
interface TranslationOptions {
  language?: string;         // Target language (default: "zh-CN")
  quality?: 'standard' | 'high';
  speakerDiarization?: boolean;
  punctuation?: boolean;
  timestamps?: boolean;
}
```

## File Upload Implementation

### uni-app File Upload

```typescript
class TranslationService {
  async uploadFile(file: UniApp.ChooseFile, type: string): Promise<UploadResponse> {
    return new Promise((resolve, reject) => {
      const token = uni.getStorageSync('token');
      
      uni.uploadFile({
        url: `${API_BASE_URL}/translation/upload`,
        filePath: file.path,
        name: 'file',
        formData: {
          type: type
        },
        header: {
          'Authorization': `Bearer ${token}`
        },
        success: (res) => {
          if (res.statusCode === 200) {
            const data = JSON.parse(res.data);
            resolve(data.data);
          } else {
            reject(new Error(`Upload failed: ${res.statusCode}`));
          }
        },
        fail: (error) => {
          reject(error);
        }
      });
    });
  }
  
  async startTranslation(uploadId: string, options: TranslationOptions): Promise<TranslationTask> {
    const response = await api.post('/translation/start', {
      uploadId,
      options
    });
    return response.data;
  }
  
  async getTranslationStatus(taskId: string): Promise<TranslationTask> {
    const response = await api.get(`/translation/${taskId}/status`);
    return response.data;
  }
}
```

### Progress Polling

```typescript
class TranslationPoller {
  private pollInterval: number = 2000; // 2 seconds
  private maxPolls: number = 150;      // 5 minutes max
  
  async pollUntilComplete(taskId: string): Promise<TranslationTask> {
    let polls = 0;
    
    while (polls < this.maxPolls) {
      try {
        const task = await translationService.getTranslationStatus(taskId);
        
        if (task.status === 'completed') {
          return task;
        }
        
        if (task.status === 'failed') {
          throw new Error(task.metadata.error || 'Translation failed');
        }
        
        // Update UI with progress
        this.updateProgress(task.progress, task.currentStep);
        
        // Wait before next poll
        await this.sleep(this.pollInterval);
        polls++;
        
      } catch (error) {
        throw error;
      }
    }
    
    throw new Error('Translation timeout');
  }
  
  private updateProgress(progress: number, step: string): void {
    // Update UI components
    store.setTranslationProgress(progress, step);
  }
  
  private sleep(ms: number): Promise<void> {
    return new Promise(resolve => setTimeout(resolve, ms));
  }
}
```

## Quota Management

### Quota Validation

```python
# FastAPI quota checking
async def check_user_quota(user_id: int) -> QuotaStatus:
    user = await get_user(user_id)
    
    if user.quota_used >= user.quota_limit:
        raise QuotaExceededError(
            quota_used=user.quota_used,
            quota_limit=user.quota_limit
        )
    
    return QuotaStatus(
        remaining=user.quota_limit - user.quota_used,
        limit=user.quota_limit
    )

async def deduct_quota(user_id: int, task_id: str):
    """Deduct quota after successful translation"""
    async with database.transaction():
        await user_service.increment_quota_used(user_id)
        await translation_service.mark_quota_used(task_id)
```

### Quota Error Handling

```typescript
// uni-app quota error handling
const handleQuotaError = (error: ApiError) => {
  if (error.code === 'QUOTA_EXCEEDED') {
    uni.showModal({
      title: '翻译次数已用完',
      content: '您的免费翻译次数已用完，升级VIP套餐可获得更多翻译次数',
      confirmText: '升级VIP',
      success: (res) => {
        if (res.confirm) {
          uni.navigateTo({ url: '/pages/subscription/subscription' });
        }
      }
    });
  }
};
```

## Error Handling

### Error Response Format

```typescript
interface TranslationError {
  success: false;
  error: {
    code: string;
    message: string;
    details?: {
      quotaUsed?: number;
      quotaLimit?: number;
      upgradeUrl?: string;
    };
  };
}
```

### Common Error Codes

| Error Code | HTTP Status | Description |
|------------|-------------|-------------|
| `INVALID_FILE_TYPE` | 400 | Unsupported file format |
| `FILE_TOO_LARGE` | 413 | File exceeds size limit |
| `QUOTA_EXCEEDED` | 402 | User quota exceeded |
| `TASK_NOT_FOUND` | 404 | Translation task not found |
| `PROCESSING_FAILED` | 500 | Transcription processing failed |
| `SERVICE_UNAVAILABLE` | 503 | Third-party service unavailable |

## Testing

### Unit Tests

```python
# FastAPI translation API tests
async def test_file_upload_success(client, authenticated_user):
    with open("test_audio.mp3", "rb") as f:
        response = await client.post(
            "/api/v1/translation/upload",
            files={"file": ("test.mp3", f, "audio/mpeg")},
            data={"type": "audio"},
            headers={"Authorization": f"Bearer {authenticated_user.token}"}
        )
    
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "uploadId" in data["data"]

async def test_quota_exceeded(client, user_with_zero_quota):
    response = await client.post(
        "/api/v1/translation/upload",
        files={"file": ("test.mp3", b"fake audio", "audio/mpeg")},
        data={"type": "audio"},
        headers={"Authorization": f"Bearer {user_with_zero_quota.token}"}
    )
    
    assert response.status_code == 402
    data = response.json()
    assert data["error"]["code"] == "QUOTA_EXCEEDED"
```

### Integration Tests

```typescript
// uni-app integration test
describe('Translation Flow', () => {
  it('should complete full translation workflow', async () => {
    // Upload file
    const uploadResult = await translationService.uploadFile(mockFile, 'audio');
    expect(uploadResult.uploadId).toBeDefined();
    
    // Start translation
    const task = await translationService.startTranslation(uploadResult.uploadId);
    expect(task.taskId).toBeDefined();
    
    // Poll for completion
    const result = await poller.pollUntilComplete(task.taskId);
    expect(result.status).toBe('completed');
    expect(result.transcription.text).toBeTruthy();
  });
});
```

## Migration Notes

### From Node.js to FastAPI

1. **File Upload Handling**: Use FastAPI's `UploadFile` for multipart uploads
2. **Async Processing**: Implement async task processing with background tasks
3. **Error Codes**: Maintain identical error codes and messages
4. **Response Format**: Preserve JSON structure and field names

### Performance Considerations

1. **File Storage**: Use CDN for file uploads and static content
2. **Processing Queue**: Implement background task queue for transcription
3. **Progress Tracking**: Real-time progress updates via WebSocket or polling
4. **Caching**: Cache transcription results to avoid reprocessing

This API contract ensures complete compatibility between uni-app frontend and FastAPI backend while maintaining all existing functionality.