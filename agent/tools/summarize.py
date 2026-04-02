"""Summarization tool using llama.cpp for text summarization."""

import subprocess
from pathlib import Path

from agent.config import Config


class SummarizeTool:
    """Summarize text using a local LLM via llama.cpp."""

    name = "summarize"
    description = "Summarize text content using local LLM"

    def __init__(self, config: Config) -> None:
        self._model_path = config.llm_model_path
        self._context_size = config.llm_context_size
        self._threads = config.llm_threads
        self._max_tokens = config.llm_max_tokens

    def _find_llama_binary(self) -> str:
        """Locate the llama.cpp binary."""
        candidates = [
            str(Path.home() / "llama.cpp" / "build" / "bin" / "llama-cli"),
            str(Path.home() / "llama.cpp" / "main"),
        ]
        for candidate in candidates:
            if Path(candidate).is_file():
                return candidate

        # Fall back to PATH lookup
        return "llama-cli"

    def _build_prompt(self, text: str) -> str:
        """Build a summarization prompt for the LLM."""
        return (
            "<|system|>\n"
            "You are a summarizer. Provide a concise summary of the following text "
            "in 2-3 sentences. Keep the summary brief and informative.\n"
            "<|user|>\n"
            f"{text}\n"
            "<|assistant|>\n"
        )

    def run(self, text: str) -> str:
        """Summarize the given text.

        Args:
            text: Text to summarize.

        Returns:
            Concise summary.
        """
        if not text.strip():
            return ""

        llama_bin = self._find_llama_binary()
        prompt = self._build_prompt(text)

        cmd = [
            llama_bin,
            "-m", self._model_path,
            "-c", str(self._context_size),
            "-t", str(self._threads),
            "-n", str(self._max_tokens),
            "--temp", "0.3",
            "-p", prompt,
            "--no-display-prompt",
        ]

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=120,
        )

        if result.returncode != 0:
            raise RuntimeError(f"llama.cpp summarization failed: {result.stderr}")

        output = result.stdout.strip()
        for token in ["<|end|>", "</s>", "<|assistant|>"]:
            output = output.replace(token, "")

        return output.strip()
