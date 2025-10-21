# DeepSeek + Qwen Setup Guide for Local LLM

## 🚀 Quick Setup for DeepSeek/Qwen Models

You've chosen to use DeepSeek + Qwen models locally, which is excellent for speech-to-text tasks and works perfectly with your requirements!

## 1. Install Ollama

**Windows:**
```powershell
# Using winget to download ollama
winget install https://ollama.com/download/windows
```

**macOS (Intel Mac):**
```bash
# Install using Homebrew
brew install ollama

# Or manual install
curl -L https://ollama.com/download/ollama-darwin-x64
```

**Linux:**
```bash
# Install using curl
curl -L https://ollama.com/download/ollama-linux-x64
```

## 2. Download DeepSeek Model

```bash
# Pull the model
ollama pull deepseek-coder:6.7b-instruct

# List available models
ollama list
```

## 3. Update Backend Configuration

**Edit `.env` file:**
```env
# Set to use Ollama with DeepSeek
STT_PROVIDER=ollama
OLLAMA_MODEL=deepseek-coder:6.7b-instruct
OLLAMA_BASE_URL=http://localhost:11434
```

## 4. Start Ollama Service

```bash
# Start Ollama server
ollama serve deepseek-coder:6.7b-instruct

# Run in background (optional)
# On Windows: Start-Process -FilePath "ollama serve ..." -ArgumentList "deepseek-coder:6.7b-instruct"
```

## 5. Test the Setup

```bash
# Test Ollama connection
python -c "
import aiohttp
import asyncio

async def test_ollama():
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get('http://localhost:11434/api/tags', timeout=5) as response:
                if response.status == 200:
                    models = await response.json()
                    available = 'deepseek-coder:6.7b-instruct' in [m.get('name', '') for m in models.get('models', [])]
                    print(f'✅ DeepSeek model available: {available}')
                    return True
                else:
                    print('❌ Ollama server not responding')
                    return False
    except Exception as e:
        print(f'❌ Connection failed: {e}')
        return False

asyncio.run(test_ollama())
"

# Test transcription
python -c "
import asyncio
from app.services.ollama_stt import OllamaSpeechToTextService

async def test_transcription():
    service = OllamaSpeechToTextService()
    if await service.test_connection():
        print('✅ Ollama connection successful')
        print('Model info:', await service.get_model_info())
    else:
        print('❌ Ollama connection failed')
        return

asyncio.run(test_transcription())
"
```

## 6. Start the Python Backend

```bash
# Activate virtual environment
venv\Scripts\activate

# Start the server
python run.py

# The backend will now use DeepSeek via Ollama!
```

## 🔧 Configuration Options

**Model Selection:**
```env
# Available DeepSeek models
OLLAMA_MODEL=deepseek-coder:6.7b-instruct
OLLAMA_MODEL=deepseek-2.5b-mml
OLLAMA_MODEL=deepseek-v3-lite
```

**Performance Tuning:**
```env
# Adjust based on your GPU/CPU capabilities
OLLAMA_MAX_TOKENS=4096    # 4K tokens max
OLLAMA_TIMEOUT=600         # 10 minute timeout
```

## 🎯 Advantages of This Setup

- ✅ **No API Keys Required**: Models run locally
- ✅ **Unlimited Usage**: No rate limits or API costs  
- ✅ **Privacy**: All processing stays on your machine
- ✅ **High Quality**: DeepSeek models are excellent for technical content
- ✅ **Full Control**: Use specific model versions and parameters
- ✅ **Cost Effective**: One-time model download vs. ongoing API costs
- ✅ **Internet Independent**: Works without internet for transcription

## 🚨 Resources Required

**System Requirements:**
- **RAM**: 16GB+ for DeepSeek-Coder models
- **Storage**: 8GB+ for model files
- **GPU**: CUDA GPU recommended but CPU works fine

**Hardware Recommendations:**
- **GPU**: NVIDIA GTX 1080Ti+ or RTX 4090+
- **CPU**: 8+ cores, 32GB+ RAM for smooth operation

This setup gives you complete control over the speech-to-text functionality without any external dependencies!