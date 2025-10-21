# Installation Troubleshooting Guide

## Problem: torch-audio package not found

This is a common issue with PyTorch audio installations. Here are several solutions:

## Solution 1: Use Stable Version (Recommended)

```bash
cd backend
pip install -r requirements.stable.txt
```

## Solution 2: Install without problematic packages

```bash
cd backend
pip install -r requirements.minimal.txt
```

## Solution 3: Install packages manually in correct order

```bash
# Step 1: Install core requirements
pip install fastapi uvicorn python-multipart python-jose[cryptography] pymongo redis pydantic aiofiles python-dotenv

# Step 2: Install PyTorch
pip install torch==2.1.0 torchaudio==2.1.0

# Step 3: Install Whisper
pip install openai-whisper==20231117

# Step 4: Install other packages
pip install googletrans==4.0.0rc1 pydub==0.25.1 pillow numpy

# Step 5: Install optional packages
pip install transformers moviepy opencv-python librosa
```

## Solution 4: Use CPU-only version (if GPU issues)

```bash
# CPU-only PyTorch (more compatible)
pip install torch==2.1.0+cpu --index-url https://download.pytorch.org/whl/cpu/torch_stable.html
pip install torchaudio==2.1.0+cpu --index-url https://download.pytorch.org/whl/cpu/torchaudio_stable.html
```

## Solution 5: Check Python Version

Ensure you're using Python 3.9+:

```bash
python --version
```

If using Python 3.11, some packages may not be available. Use Python 3.9 or 3.10:

```bash
# Create virtual environment with Python 3.9
pyenv install 3.9.18
pyenv local 3.9.18
```

## Alternative: Use Conda

```bash
# Create conda environment
conda create -n ai-media-backend python=3.9
conda activate ai-media-backend

# Install PyTorch with conda
conda install pytorch torchvision torchaudio pytorch-cuda=11.8 -c pytorch -c nvidia

# Install other packages
pip install fastapi uvicorn python-multipart pymongo redis pydantic
pip install openai-whisper googletrans pydub aiofiles
```

## Verify Installation

```bash
# Check PyTorch installation
python -c "import torch; print('PyTorch version:', torch.__version__)"

# Check torchaudio installation
python -c "import torchaudio; print('torchaudio version:', torchaudio.__version__)"

# Check Whisper installation
python -c "import whisper; print('Whisper version:', whisper.__version__)"
```

## Simplified Setup (No AI/ML Dependencies)

If you want to start without AI/ML libraries first:

```bash
pip install fastapi uvicorn python-multipart python-jose[cryptography] pymongo redis pydantic aiofiles python-dotenv

# Update environment (set STT provider to mock)
echo "STT_PROVIDER=mock" >> .env
echo "TRANSLATION_PROVIDER=mock" >> .env
```

This will give you a working API server, and you can add AI features later.

## Next Steps

1. Try Solution 1 (stable versions)
2. If that fails, try Solution 2 (minimal requirements) 
3. Use Solution 4 if you have GPU compatibility issues
4. Verify with the commands above

The API should work once the dependencies are installed successfully!