# DEEPSEEK + OLLAMA 音频/视频处理配置指南

## 🎯 概述

本指南将帮助您配置 DeepSeek + Ollama 来处理音频和视频文件的语音转文字转录。

## 📋 系统要求

### 硬件要求
- **内存**: 16GB+ (推荐用于 DeepSeek 模型)
- **存储**: 8GB+ (用于模型文件)
- **GPU**: NVIDIA GTX 1080Ti+ 或 RTX 4090+ (推荐)
- **操作系统**: Windows 10+, macOS, Linux

### 必需软件
- **Python**: 3.11+
- **Ollama**: 本地 AI 模型运行时
- **FFmpeg**: 音频/视频处理
- **MongoDB**: 数据库

## 🚀 安装步骤

### 1. 安装 Ollama

**Windows:**
```powershell
# 使用 winget 下载 Ollama
winget install https://ollama.com/download/windows

# 或手动下载安装包
# https://ollama.com/download/windows
```

**macOS:**
```bash
# 使用 Homebrew 安装
brew install ollama

# 或手动安装
curl -L https://ollama.com/download/darwin-x64 -o ollama-darwin
chmod +x ollama-darwin
sudo mv ollama-darwin /usr/local/bin/ollama
```

**Linux:**
```bash
curl -L https://ollama.com/download/linux-x64 -o ollama-linux
chmod +x ollama-linux
sudo mv ollama-linux /usr/local/bin/ollama
```

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

### 3. 启动 Ollama 服务

```bash
# 启动 Ollama 服务
ollama serve

# 或者在后台运行 (推荐)
# Windows:
Start-Process -FilePath "ollama" -ArgumentList "serve" -WindowStyle Hidden

# macOS/Linux:
nohup ollama serve > /dev/null 2>&1 &
```

### 4. 下载 DeepSeek 模型

```bash
# 下载推荐的 DeepSeek 模型
ollama pull deepseek-coder:6.7b-instruct

# 可选：下载其他 DeepSeek 模型
ollama pull deepseek-2.5b-mml
ollama pull deepseek-v3-lite

# 验证模型下载
ollama list
```

## ⚙️ 配置后端

### 1. 环境配置

创建或编辑 `.env` 文件：

```env
# 服务器配置
HOST=127.0.0.1
PORT=8001
DEBUG=true

# 使用 DeepSeek + Ollama
STT_PROVIDER=ollama
OLLAMA_MODEL=deepseek-coder:6.7b-instruct
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_TIMEOUT=600
OLLAMA_MAX_TOKENS=4096

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

### 2. 依赖安装

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
pip install -r requirements.openai.txt

# 或手动安装关键依赖
pip install fastapi uvicorn motor pymongo pydantic aiofiles
pip install python-multipart python-jose[cryptography] passlib[bcrypt]
pip install aiohttp asyncio
```

### 3. 验证配置

```bash
# 测试 Ollama 连接
python -c "
import aiohttp
import asyncio

async def test():
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get('http://localhost:11434/api/tags', timeout=5) as response:
                if response.status == 200:
                    models = await response.json()
                    available = 'deepseek-coder:6.7b-instruct' in [m.get('name', '') for m in models.get('models', [])]
                    print(f'✅ DeepSeek 模型可用: {available}')
                    return True
                else:
                    print('❌ Ollama 服务器未响应')
                    return False
    except Exception as e:
        print(f'❌ 连接失败: {e}')
        return False

asyncio.run(test())
"
```

## 🧪 测试系统

### 1. 运行完整测试

```bash
# 运行音频/视频处理测试
python test_deepseek_audio.py
```

### 2. 手动测试音频处理

```bash
# 测试音频文件处理
python -c "
import asyncio
from app.services.speech_to_text import DeepSeekSpeechToTextService

async def test():
    service = DeepSeekSpeechToTextService()
    
    if await service.test_connection():
        print('✅ DeepSeek 连接成功')
        
        # 模型信息
        info = await service.get_model_info()
        print(f'模型信息: {info}')
    else:
        print('❌ DeepSeek 连接失败')

asyncio.run(test())
"
```

### 3. 测试 API 上传

```bash
# 启动后端服务器
python run.py

# 在另一个终端测试上传
curl -X POST "http://127.0.0.1:8001/api/v1/upload" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "file=@test_audio.mp3" \
  -F "language=auto" \
  -F "model=deepseek-1" \
  -F "speaker_diarization=true"
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
  -F "speaker_diarization=true"

# 视频文件
curl -X POST "http://127.0.0.1:8001/api/v1/upload" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "file=@video.mp4" \
  -F "language=en" \
  -F "model=deepseek-1"
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

# 下载 VTT 字幕文件
curl -X GET "http://127.0.0.1:8001/api/v1/upload/JOB_ID_HERE/download?format=vtt" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -o transcription.vtt
```

## 🔧 故障排除

### 常见问题

**1. Ollama 连接失败**
```bash
# 检查 Ollama 状态
curl http://localhost:11434/api/tags

# 重启 Ollama 服务
ollama serve
```

**2. DeepSeek 模型未找到**
```bash
# 列出可用模型
ollama list

# 下载 DeepSeek 模型
ollama pull deepseek-coder:6.7b-instruct
```

**3. FFmpeg 未安装**
```bash
# 检查 FFmpeg 安装
ffmpeg -version

# 重新安装 FFmpeg
# 根据您的操作系统参考安装部分
```

**4. 内存不足**
```bash
# 监控内存使用
# Windows: 任务管理器
# macOS/Linux: htop

# 释放 Ollama 内存
ollama stop
ollama serve
```

**5. 转录质量不佳**
- 确保音频质量良好（16kHz+）
- 检查背景噪音水平
- 尝试不同的 DeepSeek 模型

### 调试命令

```bash
# 检查配置
python debug_config.py

# 检查数据库
python debug_database.py

# 实时监控
python monitor_realtime.py

# API 调试
python debug_api.py
```

## 📊 性能优化

### 1. 硬件优化
- **RAM**: 32GB+ 用于大型模型
- **GPU**: NVIDIA RTX 4090 或更新
- **存储**: SSD 用于更好的 I/O 性能

### 2. 软件优化
```env
# 调整 Ollama 参数
OLLAMA_MAX_TOKENS=4096    # 平衡质量和速度
OLLAMA_TIMEOUT=300         # 5 分钟超时

# 调整批处理设置
MAX_CONCURRENT_JOBS=1       # DeepSeek 需要更多资源
JOB_TIMEOUT_MINUTES=30     # 更长的处理时间
```

### 3. 模型选择

根据需求选择合适的 DeepSeek 模型：

- **deepseek-coder:6.7b-instruct**: 技术内容转录最佳
- **deepseek-2.5b-mml**: 多语言性能优秀
- **deepseek-v3-lite**: 资源占用较低

## 🎯 优势

✅ **本地处理**: 数据无需上传到外部服务器  
✅ **无限制使用**: 没有 API 限制或费用  
✅ **隐私保护**: 所有处理都在本地进行  
✅ **高精度**: DeepSeek 模型对技术内容特别出色  
✅ **多语言支持**: 支持 40+ 种语言  
✅ **完全控制**: 可自定义模型参数和处理流程  
✅ **离线工作**: 无需互联网连接即可转录  

现在您已经可以使用 DeepSeek + Ollama 来处理音频和视频文件的语音转文字了！ 🚀