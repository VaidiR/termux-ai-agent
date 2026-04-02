"""Whisper.cpp wrapper for audio transcription."""

import subprocess
import tempfile
from pathlib import Path

from agent.config import Config


class TranscribeTool:
    """Transcribe audio files using whisper.cpp.

    Converts .opus files to .wav via ffmpeg, then runs whisper.cpp
    for speech-to-text transcription.
    """

    name = "transcribe"
    description = "Transcribe an audio file (.opus) to text using whisper.cpp"

    def __init__(self, config: Config) -> None:
        self._model_path = config.whisper_model_path
        self._language = config.whisper_language
        self._threads = config.whisper_threads

    def _convert_to_wav(self, input_path: str, wav_path: str) -> None:
        """Convert audio file to 16kHz mono WAV for whisper.cpp."""
        cmd = [
            "ffmpeg", "-y",
            "-i", input_path,
            "-ar", "16000",
            "-ac", "1",
            "-c:a", "pcm_s16le",
            wav_path,
        ]
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=60,
        )
        if result.returncode != 0:
            raise RuntimeError(f"ffmpeg conversion failed: {result.stderr}")

    def _run_whisper(self, wav_path: str) -> str:
        """Run whisper.cpp on a WAV file and return transcription."""
        whisper_bin = self._find_whisper_binary()
        cmd = [
            whisper_bin,
            "-m", self._model_path,
            "-l", self._language,
            "-t", str(self._threads),
            "--no-timestamps",
            "-f", wav_path,
        ]
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=120,
        )
        if result.returncode != 0:
            raise RuntimeError(f"whisper.cpp failed: {result.stderr}")

        return result.stdout.strip()

    def _find_whisper_binary(self) -> str:
        """Locate the whisper.cpp binary."""
        candidates = [
            str(Path.home() / "whisper.cpp" / "build" / "bin" / "whisper-cli"),
            str(Path.home() / "whisper.cpp" / "main"),
        ]
        # Check absolute paths first
        for candidate in candidates:
            if Path(candidate).is_file():
                return candidate

        # Fall back to PATH lookup
        return "whisper-cpp"

    def run(self, audio_path: str) -> str:
        """Transcribe an audio file to text.

        Args:
            audio_path: Path to the audio file (.opus, .wav, .mp3, etc.)

        Returns:
            Transcribed text.
        """
        input_path = Path(audio_path)
        if not input_path.exists():
            raise FileNotFoundError(f"Audio file not found: {audio_path}")

        if input_path.suffix == ".wav":
            return self._run_whisper(audio_path)

        with tempfile.NamedTemporaryFile(suffix=".wav", delete=True) as tmp:
            wav_path = tmp.name
            self._convert_to_wav(audio_path, wav_path)
            return self._run_whisper(wav_path)
