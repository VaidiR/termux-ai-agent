"""Translation tool using llama.cpp for Hindi to Tamil translation."""

import os
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

        # Use a temp file for output capture.
        # llama.cpp writes generated text directly to the TTY (not stdout),
        # so subprocess pipe capture gets nothing. Shell-level redirection
        # to a file is the reliable way to capture the output.
        out_fd, out_path = tempfile.mkstemp(suffix=".txt")
        os.close(out_fd)

        try:
            shell_cmd = (
                f'"{llama_bin}"'
                f' -m "{self._model_path}"'
                f' -c {self._context_size}'
                f' -t {self._threads}'
                f' -n {self._max_tokens}'
                f' --temp 0.1'
                f' -f "{prompt_file}"'
                f' --no-display-prompt'
                f' -no-cnv'
                f' > "{out_path}" 2>/dev/null'
            )

            subprocess.run(
                shell_cmd,
                shell=True,
                timeout=120,
            )

            output = Path(out_path).read_text().strip()
        finally:
            Path(prompt_file).unlink(missing_ok=True)
            Path(out_path).unlink(missing_ok=True)

        # Clean up any trailing special tokens
        for token in ["<|end|>", "</s>", "<|assistant|>"]:
            output = output.replace(token, "")

        return output.strip()
