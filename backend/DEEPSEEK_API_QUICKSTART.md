# DeepSeek API 快速开始指南

## ✅ 状态：配置完成

您的 DeepSeek API 配置已经成功！测试结果显示：

- ✅ **API 连接正常**
- ✅ **服务导入成功** 
- ✅ **音频处理器可用**
- ✅ **文件系统正常**

## 🚀 立即使用

### 1. 启动后端服务

```bash
# 进入后端目录
cd D:\Python\startup\AI-Tools-Colllection\backend

# 启动服务器
python run.py
```

服务器将在 `http://127.0.0.1:8001` 启动

### 2. 上传音频文件测试

```bash
# 使用 curl 上传音频文件
curl -X POST "http://127.0.0.1:8001/api/v1/upload" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "file=@your_audio.mp3" \
  -F "language=zh" \
  -F "enable_timestamps=true"
```

### 3. 监控转录进度

```bash
# 使用返回的 job_id 查看进度
curl -X GET "http://127.0.0.1:8001/api/v1/upload/JOB_ID_HERE" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### 4. 下载转录结果

```bash
# 下载 JSON 格式结果
curl -X GET "http://127.0.0.1:8001/api/v1/upload/JOB_ID_HERE/download?format=json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -o transcription.json
```

## 📁 支持的文件格式

### 音频文件
- ✅ MP3, WAV, M4A, AAC, OGG, FLAC
- ✅ 自动格式优化
- ✅ 采样率自动调整

### 视频文件  
- ✅ MP4, MOV, AVI, MKV, WebM
- ✅ 自动提取音频
- ✅ 音频转录

## 🌐 支持的语言

DeepSeek API 支持 40+ 种语言，包括：
- 🇨🇳 中文 (zh)
- 🇺🇸 英语 (en)  
- 🇪🇸 西班牙语 (es)
- 🇫🇷 法语 (fr)
- 🇩🇪 德语 (de)
- 🇯🇵 日语 (ja)
- 🇰🇷 韩语 (ko)
- 等等...

## 🔧 API 参数

```python
transcription_options = {
    "language": "auto",              # 自动检测语言
    "enable_timestamps": True,       # 包含时间戳
    "enable_speaker_diarization": True,  # 说话人分离
    "response_format": "json"        # 响应格式
}
```

## 💡 使用提示

### 1. 文件大小限制
- **推荐**: 音频文件 < 25MB
- **最大**: 100MB (视频文件)
- **API 限制**: 具体限制请查看 DeepSeek 文档

### 2. 转录质量优化
- 使用清晰的音频录制
- 减少背景噪音
- 选择合适的采样率 (16kHz 最佳)
- 单声道效果更好

### 3. 错误处理
- 网络超时: 自动重试机制
- 格式不支持: 自动转换
- API 限流: 智能排队处理

## 📊 结果格式

```json
{
  "full_text": "完整的转录文本",
  "segments": [
    {
      "start": 0.0,
      "end": 5.2,
      "text": "第一段文本",
      "confidence": 0.95
    }
  ],
  "language": "zh",
  "confidence": 0.92,
  "metadata": {
    "provider": "deepseek_api",
    "model": "deepseek-audio",
    "processing_method": "deepseek_api_transcription",
    "file_info": {
      "original_path": "path/to/file",
      "file_type": "audio",
      "media_duration": 30.5,
      "file_size": 1024000
    }
  }
}
```

## 🔍 故障排除

### 常见问题

**Q: 转录失败怎么办？**
A: 检查音频文件格式、网络连接、API 密钥有效性

**Q: 支持实时转录吗？**
A: 当前是批处理模式，可以上传短文件实现准实时

**Q: 如何提高转录精度？**
A: 使用高质量音频、合适的语言设置、减少噪音

**Q: API 配额用完了？**
A: 检查 DeepSeek 控制台的用量统计，升级套餐

## 📞 技术支持

- 📚 **完整文档**: `DEEPSEEK_API_GUIDE.md`
- 🧪 **测试脚本**: `test_deepseek_simple.py`
- ⚙️ **配置检查**: `test_config_only.py`

---

🎉 **恭喜！您的 DeepSeek API 语音转文字服务已经可以正常使用了！**

现在您可以：
1. 启动后端服务器
2. 通过 API 上传音频/视频文件
3. 获得高质量的转录结果