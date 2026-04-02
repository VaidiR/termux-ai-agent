"""Configuration management for the Termux AI Agent."""

import os
from pathlib import Path
from typing import Any

import yaml


DEFAULT_CONFIG = {
    "whisper": {
        "model_path": "models/ggml-tiny.bin",
        "language": "hi",
        "threads": 2,
    },
    "llm": {
        "model_path": "models/tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf",
        "context_size": 512,
        "threads": 2,
        "max_tokens": 256,
    },
    "agent": {
        "max_steps": 10,
        "csv_path": "data/tracking.csv",
    },
}


class Config:
    """Manages configuration from YAML file and environment variables."""

    def __init__(self, config_path: str = "config.yaml") -> None:
        self._config: dict[str, Any] = {}
        self._config_path = Path(config_path)
        self._load()

    def _load(self) -> None:
        """Load configuration from YAML file, falling back to defaults."""
        if self._config_path.exists():
            with open(self._config_path, "r") as f:
                file_config = yaml.safe_load(f) or {}
            self._config = self._merge(DEFAULT_CONFIG, file_config)
        else:
            self._config = DEFAULT_CONFIG.copy()

        self._apply_env_overrides()

    def _merge(self, base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
        """Deep merge override into base."""
        result = base.copy()
        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._merge(result[key], value)
            else:
                result[key] = value
        return result

    def _apply_env_overrides(self) -> None:
        """Apply environment variable overrides (TERMUX_AI_ prefix)."""
        env_map = {
            "TERMUX_AI_WHISPER_MODEL": ("whisper", "model_path"),
            "TERMUX_AI_WHISPER_LANG": ("whisper", "language"),
            "TERMUX_AI_WHISPER_THREADS": ("whisper", "threads"),
            "TERMUX_AI_LLM_MODEL": ("llm", "model_path"),
            "TERMUX_AI_LLM_CONTEXT": ("llm", "context_size"),
            "TERMUX_AI_LLM_THREADS": ("llm", "threads"),
            "TERMUX_AI_LLM_MAX_TOKENS": ("llm", "max_tokens"),
            "TERMUX_AI_MAX_STEPS": ("agent", "max_steps"),
            "TERMUX_AI_CSV_PATH": ("agent", "csv_path"),
        }

        for env_var, (section, key) in env_map.items():
            value = os.environ.get(env_var)
            if value is not None:
                existing = self._config[section][key]
                if isinstance(existing, int):
                    self._config[section][key] = int(value)
                else:
                    self._config[section][key] = value

    @property
    def whisper_model_path(self) -> str:
        return str(self._config["whisper"]["model_path"])

    @property
    def whisper_language(self) -> str:
        return str(self._config["whisper"]["language"])

    @property
    def whisper_threads(self) -> int:
        return int(self._config["whisper"]["threads"])

    @property
    def llm_model_path(self) -> str:
        return str(self._config["llm"]["model_path"])

    @property
    def llm_context_size(self) -> int:
        return int(self._config["llm"]["context_size"])

    @property
    def llm_threads(self) -> int:
        return int(self._config["llm"]["threads"])

    @property
    def llm_max_tokens(self) -> int:
        return int(self._config["llm"]["max_tokens"])

    @property
    def max_steps(self) -> int:
        return int(self._config["agent"]["max_steps"])

    @property
    def csv_path(self) -> str:
        return str(self._config["agent"]["csv_path"])

    def as_dict(self) -> dict[str, Any]:
        """Return full config as dictionary."""
        return self._config.copy()
