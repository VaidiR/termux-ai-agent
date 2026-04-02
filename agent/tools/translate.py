"""Translation tool using llama.cpp for Hindi to Tamil translation."""

import subprocess
import tempfile
from pathlib import Path

from agent.config import Config


class TranslateTool:
    """Translate text from Hindi to Tamil using a local LLM via llama.cpp."""

    name = "translate"
    description = "Translate Hindi text to Tamil using local LLM"

    def __init__(self, config: Config) -> None:
        self._model_path = config.llm_model_path
        self._context_size = config.llm_context_size
        self._threads = config.llm_threads
        self._max_tokens = config.llm_max_tokens

    def _find_llama_binary(self) -> str:
        """Locate the llama.cpp completion binary.

        Uses llama-completion (not llama-cli) because llama-cli does not
        support --no-conversation and writes output directly to the TTY,
        making it impossible to capture via subprocess pipes.
        """
        candidates = [
            str(Path.home() / "llama.cpp" / "build" / "bin" / "llama-completion"),
            str(Path.home() / "llama.cpp" / "build" / "bin" / "llama-cli"),
            str(Path.home() / "llama.cpp" / "main"),
        ]
        for candidate in candidates:
            if Path(candidate).is_file():
                return candidate

        # Fall back to PATH lookup
        return "llama-completion"

    def _build_prompt(self, text: str) -> str:
        """Build a translation prompt for the LLM."""
        return (
            "<|system|>\n"
            "You are a translator. Translate the following Hindi text to Tamil. "
            "Output only the Tamil translation, nothing else.\n"
            "<|user|>\n"
            f"{text}\n"
            "<|assistant|>\n"
        )

    def run(self, text: str) -> str:
        """Translate Hindi text to Tamil.

        Args:
            text: Hindi text to translate.

        Returns:
            Tamil translation.
        """
        if not text.strip():
            return ""

        llama_bin = self._find_llama_binary()
        prompt = self._build_prompt(text)

        # Write prompt to a temp file to avoid shell escaping issues
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".txt", delete=False
        ) as tmp:
            tmp.write(prompt)
            prompt_file = tmp.name

        try:
            cmd = [
                llama_bin,
                "-m", self._model_path,
                "-c", str(self._context_size),
                "-t", str(self._threads),
                "-n", str(self._max_tokens),
                "--temp", "0.1",
                "-f", prompt_file,
                "--no-display-prompt",
                "-no-cnv",
                "--log-disable",
            ]

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=120,
            )
        finally:
            Path(prompt_file).unlink(missing_ok=True)

        if result.returncode != 0:
            raise RuntimeError(f"llama.cpp translation failed: {result.stderr}")

        output = result.stdout.strip()
        # Clean up any trailing special tokens
        for token in ["<|end|>", "</s>", "<|assistant|>"]:
            output = output.replace(token, "")

        return output.strip()
