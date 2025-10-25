# DEEPSEEK API 语音转文字配置指南

## 🎯 概述

本指南将帮助您配置 DeepSeek API 来处理音频和视频文件的语音转文字转录。

## 📋 前置要求

### API 密钥
- **DeepSeek API Key**: 从 [DeepSeek Platform](https://platform.deepseek.com/) 获取
- **订阅**: 需要 DeepSeek API 订阅服务
- **权限**: 确保您的 API 密钥有语音转文字权限

### 必需软件
- **Python**: 3.11+
- **FFmpeg**: 音频/视频处理
- **MongoDB**: 数据库
- **Redis**: 缓存和进度跟踪

## 🚀 配置步骤

### 1. 获取 DeepSeek API 密钥

1. 访问 [DeepSeek Platform](https://platform.deepseek.com/)
2. 注册或登录账户
3. 前往 API Keys 页面
4. 创建新的 API 密钥
5. 确保密钥有语音转文字权限

### 2. 安装 FFmpeg

**Windows:**
```powershell
# 使用 Chocolatey
choco install ffmpeg

# 或下载预编译版本
# https://ffmpeg.org/download.html
```

**macOS:**
```bash
brew install ffmpeg
```

**Linux (Ubuntu/Debian):**
```bash
sudo apt update
sudo apt install ffmpeg
```

### 3. 环境配置

编辑 `.env` 文件：

```env
# 服务器配置
HOST=127.0.0.1
PORT=8001
DEBUG=true

# 使用 DeepSeek API
STT_PROVIDER=deepseek_api
DEEPSEEK_API_KEY=your_deepseek_api_key_here

# 数据库配置
MONGODB_URI=mongodb://localhost:27017/ai_media_translation
REDIS_URL=redis://localhost:6379

# JWT 配置
JWT_SECRET=your-super-secret-jwt-key-change-this-in-production
ACCESS_TOKEN_EXPIRE_MINUTES=1440

# 文件上传配置
UPLOAD_DIR=./uploads
TEMP_DIR=./temp
MAX_FILE_SIZE=104857600  # 100MB
```

### 4. 依赖安装

```bash
cd backend

# 创建虚拟环境（如果还没有）
python -m venv venv

# 激活虚拟环境
# Windows:
venv\Scripts\activate

# macOS/Linux:
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt
```

## 🧪 测试配置

### 1. 运行配置测试

```bash
# 测试 DeepSeek API 配置
python test_deepseek_api.py
```

### 2. 验证 API 连接

```bash
# 手动测试 API 连接
python -c "
import asyncio
from app.services.deepseek_api_stt import DeepSeekAPISpeechToTextService

async def test():
    service = DeepSeekAPISpeechToTextService()
    
    if await service.test_connection():
        print('✅ DeepSeek API 连接成功')
        
        # 模型信息
        info = await service.get_model_info()
        print(f'模型信息: {info}')
    else:
        print('❌ DeepSeek API 连接失败')

asyncio.run(test())
"
```

### 3. 测试音频处理

```bash
# 测试音频文件转录
python -c "
import asyncio
from app.services.deepseek_api_stt import DeepSeekAPISpeechToTextService

async def test():
    service = DeepSeekAPISpeechToTextService()
    
    # 测试转录（需要音频文件）
    result = await service.transcribe('test_audio.mp3', {
        'language': 'auto',
        'enable_timestamps': True
    })
    
    print('转录结果:', result.get('full_text', '')[:100])

asyncio.run(test())
"
```

## 📝 使用方法

### 1. 上传文件

通过 API 上传音频或视频文件：

```bash
# 音频文件
curl -X POST "http://127.0.0.1:8001/api/v1/upload" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "file=@audio.mp3" \
  -F "language=zh" \
  -F "enable_timestamps=true"

# 视频文件
curl -X POST "http://127.0.0.1:8001/api/v1/upload" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "file=@video.mp4" \
  -F "language=en" \
  -F "enable_timestamps=true"
```

### 2. 监控转录进度

```bash
# 使用作业 ID 监控进度
curl -X GET "http://127.0.0.1:8001/api/v1/upload/JOB_ID_HERE" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### 3. 下载结果

```bash
# 下载 JSON 格式结果
curl -X GET "http://127.0.0.1:8001/api/v1/upload/JOB_ID_HERE/download?format=json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -o transcription.json

# 下载 SRT 字幕文件
curl -X GET "http://127.0.0.1:8001/api/v1/upload/JOB_ID_HERE/download?format=srt" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -o transcription.srt
```

## 🔧 高级配置

### 1. 自定义模型参数

```env
# DeepSeek API 高级配置
DEEPSEEK_API_MODEL=deepseek-audio
DEEPSEEK_API_TIMEOUT=300
DEEPSEEK_API_MAX_RETRIES=3
```

### 2. 语言配置

支持的语言代码：
- `en` - 英语
- `zh` - 中文
- `es` - 西班牙语
- `fr` - 法语
- `de` - 德语
- `ja` - 日语
- `ko` - 韩语
- 等等...

### 3. 转录选项

```python
transcription_options = {
    "language": "auto",              # 自动检测语言
    "enable_timestamps": True,       # 包含时间戳
    "enable_speaker_diarization": True,  # 说话人分离
    "response_format": "json"        # 响应格式
}
```

## 🔍 故障排除

### 常见问题

**1. API 密钥无效**
```bash
# 检查 API 密钥配置
echo $DEEPSEEK_API_KEY

# 验证 API 密钥
curl -H "Authorization: Bearer YOUR_API_KEY" \
     https://api.deepseek.com/v1/models
```

**2. FFmpeg 未安装**
```bash
# 检查 FFmpeg 安装
ffmpeg -version

# 重新安装 FFmpeg
# 根据您的操作系统参考安装部分
```

**3. 网络连接问题**
```bash
# 测试 DeepSeek API 连接
curl -I https://api.deepseek.com/v1/models

# 检查防火墙设置
# 确保 443 端口开放
```

**4. 文件格式不支持**
```bash
# 检查支持的格式
python -c "
from app.services.deepseek_api_stt import DeepSeekAPISpeechToTextService
service = DeepSeekAPISpeechToTextService()
print('支持的语言:', service.get_supported_languages())
"
```

**5. API 配额超限**
- 检查您的 DeepSeek API 使用配额
- 升级您的订阅计划
- 实施请求频率限制

### 调试命令

```bash
# 运行完整测试套件
python test_deepseek_api.py

# 检查配置
python -c "
from app.core.config import settings
print('STT Provider:', settings.STT_PROVIDER)
print('DeepSeek API Key:', 'Configured' if settings.DEEPSEEK_API_KEY else 'Not configured')
"

# 查看日志
tail -f logs/app.log
```

## 📊 性能优化

### 1. 音频预处理

DeepSeek API 支持多种音频格式，但推荐：
- **格式**: WAV, MP3, M4A, FLAC
- **采样率**: 16kHz
- **声道**: 单声道
- **位深度**: 16-bit

### 2. 批处理优化

```env
# 并发处理设置
MAX_CONCURRENT_JOBS=3
JOB_TIMEOUT_MINUTES=30
```

### 3. 缓存策略

- Redis 用于缓存转录结果
- 临时文件自动清理
- 进度跟踪实时更新

## 🎯 优势

✅ **高精度**: DeepSeek 模型提供准确的语音识别  
✅ **多语言支持**: 支持 40+ 种语言  
✅ **实时处理**: 快速 API 响应时间  
✅ **视频支持**: 自动提取视频中的音频  
✅ **时间戳**: 精确的词级时间戳  
✅ **说话人分离**: 自动识别不同说话人  
✅ **格式兼容**: 支持多种音频/视频格式  
✅ **可扩展性**: 云端 API，无需本地资源  

## 📚 参考文档

- [DeepSeek API 文档](https://platform.deepseek.com/docs)
- [DeepSeek API 定价](https://platform.deepseek.com/pricing)
- [项目 GitHub](https://github.com/your-repo)

现在您已经可以使用 DeepSeek API 来处理音频和视频文件的语音转文字了！ 🚀