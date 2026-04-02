#!/data/data/com.termux/files/usr/bin/bash
# ============================================================
# Termux AI Agent - Setup Script
# Optimized for ARM (OnePlus / Snapdragon devices)
# ============================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
MODELS_DIR="$SCRIPT_DIR/models"
DATA_DIR="$SCRIPT_DIR/data"

echo "============================================"
echo "  Termux AI Agent - Setup"
echo "============================================"
echo ""

# ---- Step 1: Update Termux packages ----
echo "[1/7] Updating Termux packages..."
pkg update -y && pkg upgrade -y

# ---- Step 2: Install system dependencies ----
echo "[2/7] Installing system dependencies..."
pkg install -y \
    python \
    ffmpeg \
    cmake \
    make \
    clang \
    git \
    wget

# ---- Step 3: Install Python dependencies ----
echo "[3/7] Installing Python dependencies..."
pip install --upgrade pip
pip install -r "$SCRIPT_DIR/requirements.txt"

# ---- Step 4: Build whisper.cpp ----
echo "[4/7] Building whisper.cpp..."
if [ ! -d "$HOME/whisper.cpp" ]; then
    cd "$HOME"
    git clone https://github.com/ggerganov/whisper.cpp.git
    cd whisper.cpp
    make -j2 CFLAGS="-O2" CXXFLAGS="-O2"
else
    echo "  whisper.cpp already exists, skipping build"
    cd "$HOME/whisper.cpp"
    # Rebuild if binary is missing
    if [ ! -f "main" ]; then
        make -j2 CFLAGS="-O2" CXXFLAGS="-O2"
    fi
fi

# Make whisper accessible
if ! command -v whisper-cpp &> /dev/null; then
    ln -sf "$HOME/whisper.cpp/main" "$PREFIX/bin/whisper-cpp" 2>/dev/null || true
fi

# ---- Step 5: Build llama.cpp ----
echo "[5/7] Building llama.cpp..."
if [ ! -d "$HOME/llama.cpp" ]; then
    cd "$HOME"
    git clone https://github.com/ggerganov/llama.cpp.git
    cd llama.cpp
    make -j2 CFLAGS="-O2" CXXFLAGS="-O2"
else
    echo "  llama.cpp already exists, skipping build"
    cd "$HOME/llama.cpp"
    if [ ! -f "llama-cli" ] && [ ! -f "main" ]; then
        make -j2 CFLAGS="-O2" CXXFLAGS="-O2"
    fi
fi

# Make llama accessible
if [ -f "$HOME/llama.cpp/llama-cli" ]; then
    ln -sf "$HOME/llama.cpp/llama-cli" "$PREFIX/bin/llama-cli" 2>/dev/null || true
elif [ -f "$HOME/llama.cpp/main" ]; then
    ln -sf "$HOME/llama.cpp/main" "$PREFIX/bin/llama-cli" 2>/dev/null || true
fi

# ---- Step 6: Download models ----
echo "[6/7] Downloading models..."
mkdir -p "$MODELS_DIR"

# Whisper tiny model (~75MB)
WHISPER_MODEL="$MODELS_DIR/ggml-tiny.bin"
if [ ! -f "$WHISPER_MODEL" ]; then
    echo "  Downloading whisper tiny model (~75MB)..."
    wget -q --show-progress \
        "https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-tiny.bin" \
        -O "$WHISPER_MODEL"
else
    echo "  Whisper model already exists"
fi

# TinyLlama 1.1B Q4_K_M (~670MB)
LLM_MODEL="$MODELS_DIR/tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf"
if [ ! -f "$LLM_MODEL" ]; then
    echo "  Downloading TinyLlama 1.1B Q4 model (~670MB)..."
    wget -q --show-progress \
        "https://huggingface.co/TheBloke/TinyLlama-1.1B-Chat-v1.0-GGUF/resolve/main/tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf" \
        -O "$LLM_MODEL"
else
    echo "  LLM model already exists"
fi

# ---- Step 7: Setup data directory ----
echo "[7/7] Setting up data directory..."
mkdir -p "$DATA_DIR"

# ---- Done ----
echo ""
echo "============================================"
echo "  Setup Complete!"
echo "============================================"
echo ""
echo "Models downloaded to: $MODELS_DIR"
echo "Data directory:       $DATA_DIR"
echo ""
echo "Usage:"
echo "  cd $SCRIPT_DIR"
echo "  python cli.py process <audio.opus>"
echo "  python cli.py batch <directory>"
echo "  python cli.py interactive"
echo ""
echo "Memory tips for low-RAM devices:"
echo "  - Close other apps before running"
echo "  - Use 'threads: 1' in config.yaml if RAM is tight"
echo "  - Use whisper tiny model (already default)"
echo ""
