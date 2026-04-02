# Termux AI Agent

A lightweight agentic AI system optimized for Android Termux. Processes WhatsApp `.opus` audio files offline using a ReAct agent pattern with `llama.cpp` and `whisper.cpp`.

## Features

- **Audio Transcription**: Convert `.opus` audio files to text via `whisper.cpp`
- **Translation**: Hindi to Tamil translation using local LLM
- **Summarization**: Summarize transcribed content
- **Student Tracking**: Store all outputs in CSV format
- **Offline-First**: No internet required after initial setup
- **Low Resource**: Optimized for ARM devices with limited RAM

## Architecture

```
termux-ai-agent/
├── agent/
│   ├── __init__.py
│   ├── core.py          # ReAct agent loop
│   ├── config.py        # Configuration management
│   └── tools/
│       ├── __init__.py
│       ├── transcribe.py    # whisper.cpp wrapper
│       ├── translate.py     # Hindi→Tamil translation
│       ├── summarize.py     # Text summarization
│       └── csv_store.py     # CSV output storage
├── cli.py               # CLI entry point
├── setup.sh             # Termux setup script
├── requirements.txt     # Python dependencies
├── samples/             # Sample test files
│   └── test_audio.opus
└── data/                # Output directory
    └── tracking.csv
```

## Requirements

- Android device with Termux installed
- ~2GB free storage (for models)
- ~1GB RAM available
- ARM64 processor (most modern Android devices)

## Quick Start

### 1. Install on Termux

```bash
# Clone the repo
git clone https://github.com/YOUR_USER/termux-ai-agent.git
cd termux-ai-agent

# Run the setup script
chmod +x setup.sh
bash setup.sh
```

### 2. Download Models

The setup script will download recommended small models:
- **Whisper**: `ggml-tiny.bin` (~75MB) — fast transcription
- **LLM**: `tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf` (~670MB) — translation & summarization

### 3. Run

```bash
# Process a single audio file
python cli.py process audio.opus

# Process all .opus files in a directory
python cli.py batch /path/to/audio/files/

# View tracking data
python cli.py report

# Interactive mode
python cli.py interactive
```

## CLI Commands

| Command | Description |
|---------|-------------|
| `process <file>` | Process a single `.opus` audio file |
| `batch <directory>` | Process all `.opus` files in a directory |
| `report` | Display summary of all processed files |
| `interactive` | Start interactive agent session |
| `config` | Show current configuration |

## Configuration

Edit `config.yaml` or set environment variables:

```yaml
whisper:
  model_path: "models/ggml-tiny.bin"
  language: "hi"           # Source language (Hindi)
  threads: 2               # CPU threads for inference

llm:
  model_path: "models/tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf"
  context_size: 512        # Context window size
  threads: 2               # CPU threads for inference
  max_tokens: 256          # Max output tokens

agent:
  max_steps: 10            # Max ReAct steps per task
  csv_path: "data/tracking.csv"
```

## How It Works

The system uses a **ReAct (Reasoning + Acting)** agent pattern:

1. **Observe**: Receive an audio file as input
2. **Think**: Determine next action (transcribe → translate → summarize → store)
3. **Act**: Execute the selected tool
4. **Repeat**: Continue until all steps are complete

Each tool is modular and can be used independently or orchestrated by the agent.

## Performance

Tested on OnePlus devices (Snapdragon ARM):

| Operation | Time (approx) | RAM Usage |
|-----------|---------------|-----------|
| Transcribe (30s audio) | ~5-10s | ~200MB |
| Translate (paragraph) | ~3-8s | ~600MB |
| Summarize (paragraph) | ~3-8s | ~600MB |

## Troubleshooting

- **Out of memory**: Reduce `context_size` and `threads` in config
- **Slow inference**: Use smaller models (ggml-tiny for whisper)
- **ffmpeg errors**: Run `pkg install ffmpeg` in Termux
- **Permission denied**: Run `termux-setup-storage` first

## License

MIT
