# Termux AI Agent - Setup Guide for OnePlus 13

Step-by-step instructions to build and run the Termux AI Agent on a fresh Termux session on your OnePlus 13.

---

## Prerequisites

- **OnePlus 13** (Snapdragon 8 Elite, ARM64)
- **~3GB free storage** (project + models + build tools)
- **Android 15** (OxygenOS 15)

---

## Step 1: Install Termux

1. Install **Termux** from [F-Droid](https://f-droid.org/en/packages/com.termux/) (recommended) or the [GitHub releases](https://github.com/termux/termux-app/releases)
   > **Do NOT use the Play Store version** — it is outdated and no longer maintained.

2. Open Termux and grant storage access:
   ```bash
   termux-setup-storage
   ```
   Tap **Allow** when prompted.

---

## Step 2: Update Termux & Install Base Packages

```bash
pkg update -y && pkg upgrade -y
pkg install -y python ffmpeg cmake make clang git wget
```

This installs:
- `python` — for the agent
- `ffmpeg` — for audio conversion (.opus → .wav)
- `cmake`, `make`, `clang` — for building whisper.cpp and llama.cpp
- `git` — for cloning the repo
- `wget` — for downloading models

---

## Step 3: Clone the Repository

```bash
cd ~
git clone https://github.com/VaidiR/termux-ai-agent.git
cd termux-ai-agent
```

---

## Step 4: Install Python Dependencies

```bash
# Do NOT run 'pip install --upgrade pip' — Termux manages pip via pkg
pip install -r requirements.txt
```

---

## Step 5: Build whisper.cpp

```bash
cd ~
git clone https://github.com/ggerganov/whisper.cpp.git
cd whisper.cpp
cmake -B build -DCMAKE_BUILD_TYPE=Release
cmake --build build --config Release -j4
```

> **OnePlus 13 tip**: You can use `-j4` safely — the Snapdragon 8 Elite has plenty of cores. If Termux gets killed during build (OOM), reduce to `-j2`.

Make it accessible system-wide:
```bash
ln -sf ~/whisper.cpp/build/bin/whisper-cli $PREFIX/bin/whisper-cpp
```

Verify:
```bash
whisper-cpp --help
```

---

## Step 6: Build llama.cpp

```bash
cd ~
git clone https://github.com/ggerganov/llama.cpp.git
cd llama.cpp
cmake -B build -DCMAKE_BUILD_TYPE=Release
cmake --build build --config Release -j4
```

Make it accessible:
```bash
ln -sf ~/llama.cpp/build/bin/llama-completion $PREFIX/bin/llama-completion
```

> **Note**: The agent uses `llama-completion` (not `llama-cli`). `llama-cli` does not support `--no-conversation` mode and writes output directly to the terminal, which prevents subprocess capture.

Verify:
```bash
llama-completion --help
```

---

## Step 7: Download Models

```bash
cd ~/termux-ai-agent
mkdir -p models

# Whisper tiny model (~75MB) — fast, low RAM
wget -q --show-progress \
    "https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-tiny.bin" \
    -O models/ggml-tiny.bin

# TinyLlama 1.1B Q4_K_M (~670MB) — good balance of quality vs speed
wget -q --show-progress \
    "https://huggingface.co/TheBloke/TinyLlama-1.1B-Chat-v1.0-GGUF/resolve/main/tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf" \
    -O models/tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf
```

> **Download time**: ~5-10 minutes on WiFi depending on your connection speed.

---

## Step 8: Set Up Data Directory

```bash
cd ~/termux-ai-agent
mkdir -p data
```

---

## Step 9: Test the Installation

### Verify the CLI starts:
```bash
cd ~/termux-ai-agent
python cli.py --help
```

Expected output:
```
usage: cli.py [-h] [--config CONFIG] {process,batch,report,interactive,config} ...

Termux AI Agent - Lightweight agentic AI for Android
...
```

### Check configuration:
```bash
python cli.py config
```

Should show your model paths and settings.

---

## Step 10: Process Your First Audio File

### Option A: Use a WhatsApp voice message

WhatsApp voice notes are stored at:
```
/storage/emulated/0/Android/media/com.whatsapp/WhatsApp/Media/WhatsApp Voice Notes/
```

Copy one to the samples directory:
```bash
cp /storage/emulated/0/Android/media/com.whatsapp/WhatsApp/Media/WhatsApp\ Voice\ Notes/202*/*.opus ~/termux-ai-agent/samples/
```

Process it:
```bash
cd ~/termux-ai-agent
python cli.py process samples/your_file.opus
```

### Option B: Record a test clip

```bash
# Record 5 seconds of audio
termux-microphone-record -l 5 -f ~/test_recording.m4a

# Convert to opus
ffmpeg -i ~/test_recording.m4a -c:a libopus ~/termux-ai-agent/samples/test.opus

# Process it
cd ~/termux-ai-agent
python cli.py process samples/test.opus
```

### Option C: Batch process a folder

```bash
cd ~/termux-ai-agent
python cli.py batch samples/
```

---

## Step 11: View Results

```bash
cd ~/termux-ai-agent
python cli.py report
```

The CSV tracking data is stored at `data/tracking.csv`.

---

## Alternative: One-Command Setup

If you prefer, you can run the included setup script which does steps 2-8 automatically:

```bash
cd ~/termux-ai-agent
chmod +x setup.sh
bash setup.sh
```

> **Note**: The setup script uses `-j2` for builds (conservative). On the OnePlus 13 you can safely edit `setup.sh` and change to `-j4` for faster builds.

---

## Performance on OnePlus 13

The Snapdragon 8 Elite in the OnePlus 13 handles this well:

| Operation | Expected Time | RAM Usage |
|-----------|--------------|-----------|
| Transcribe (30s audio) | ~3-5s | ~200MB |
| Translate (paragraph) | ~2-5s | ~600MB |
| Summarize (paragraph) | ~2-5s | ~600MB |
| Full pipeline (30s audio) | ~10-15s | ~600MB peak |

The OnePlus 13 has 12-24GB RAM, so you can safely use `threads: 4` in `config.yaml` for faster inference:

```yaml
whisper:
  threads: 4
llm:
  threads: 4
  context_size: 1024
```

---

## Troubleshooting

| Issue | Fix |
|-------|-----|
| `pkg` commands fail | Run `termux-change-repo` and select a mirror |
| Build killed (OOM) | Close other apps, reduce `-j4` to `-j2` |
| `ffmpeg: command not found` | Run `pkg install ffmpeg` |
| `Permission denied` on audio | Run `termux-setup-storage` and restart Termux |
| Slow downloads | Use a WiFi connection for model downloads |
| `whisper-cpp: not found` | Re-run the `ln -sf` command from Step 5 |
| Python import errors | Run `pip install -r requirements.txt` |
| Termux gets killed in background | Enable "Don't optimize" in Android battery settings for Termux |

### Battery Optimization (Important!)

To prevent Android from killing Termux during long operations:
1. Go to **Settings → Battery → Battery optimization**
2. Find **Termux** and select **Don't optimize**
3. Also disable "Adaptive battery" for Termux in **Settings → Apps → Termux → Battery**

---

## Interactive Mode

For hands-on testing:
```bash
cd ~/termux-ai-agent
python cli.py interactive
```

Then type commands:
```
agent> process samples/test.opus
agent> report
agent> config
agent> help
agent> quit
```
