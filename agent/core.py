"""ReAct agent core loop for processing audio files."""

import sys
from pathlib import Path
from typing import Optional

from agent.config import Config
from agent.tools.transcribe import TranscribeTool
from agent.tools.translate import TranslateTool
from agent.tools.summarize import SummarizeTool
from agent.tools.csv_store import CSVStoreTool


class AgentResult:
    """Result of processing a single audio file."""

    def __init__(self, filename: str) -> None:
        self.filename = filename
        self.transcription: str = ""
        self.translation: str = ""
        self.summary: str = ""
        self.status: str = "pending"
        self.error: Optional[str] = None
        self.steps: list[str] = []

    def to_dict(self) -> dict[str, str]:
        return {
            "filename": self.filename,
            "transcription": self.transcription,
            "translation": self.translation,
            "summary": self.summary,
            "status": self.status,
            "error": self.error or "",
        }


class Agent:
    """ReAct agent that orchestrates audio processing pipeline.

    The agent follows the Reasoning + Acting pattern:
    1. Observe the current state
    2. Think about what action to take next
    3. Act by calling the appropriate tool
    4. Repeat until the task is complete or max steps reached
    """

    TOOL_ORDER = ["transcribe", "translate", "summarize", "store"]

    def __init__(self, config: Optional[Config] = None) -> None:
        self._config = config or Config()
        self._transcribe = TranscribeTool(self._config)
        self._translate = TranslateTool(self._config)
        self._summarize = SummarizeTool(self._config)
        self._csv_store = CSVStoreTool(self._config)
        self._max_steps = self._config.max_steps

    def _log(self, message: str) -> None:
        """Print a log message to stderr."""
        print(f"[agent] {message}", file=sys.stderr)

    def _think(self, result: AgentResult, step: int) -> Optional[str]:
        """Determine the next action based on current state.

        Args:
            result: Current processing result.
            step: Current step number.

        Returns:
            Name of the next tool to run, or None if done.
        """
        if step >= self._max_steps:
            self._log(f"Max steps ({self._max_steps}) reached")
            return None

        if not result.transcription:
            return "transcribe"
        if not result.translation:
            return "translate"
        if not result.summary:
            return "summarize"
        if result.status != "complete":
            return "store"

        return None

    def _act(self, action: str, result: AgentResult, audio_path: str) -> None:
        """Execute an action (tool call).

        Args:
            action: Tool name to execute.
            result: Current result to update.
            audio_path: Path to the audio file.
        """
        if action == "transcribe":
            self._log(f"Transcribing: {audio_path}")
            result.transcription = self._transcribe.run(audio_path)
            result.steps.append(f"Transcribed ({len(result.transcription)} chars)")
            self._log(f"Transcription: {result.transcription[:100]}...")

        elif action == "translate":
            self._log("Translating Hindi -> Tamil")
            result.translation = self._translate.run(result.transcription)
            result.steps.append(f"Translated ({len(result.translation)} chars)")
            self._log(f"Translation: {result.translation[:100]}...")

        elif action == "summarize":
            self._log("Summarizing content")
            result.summary = self._summarize.run(result.transcription)
            result.steps.append(f"Summarized ({len(result.summary)} chars)")
            self._log(f"Summary: {result.summary[:100]}...")

        elif action == "store":
            self._log("Storing results in CSV")
            msg = self._csv_store.run(
                filename=result.filename,
                transcription=result.transcription,
                translation=result.translation,
                summary=result.summary,
            )
            result.status = "complete"
            result.steps.append("Stored in CSV")
            self._log(msg)

    def process(self, audio_path: str) -> AgentResult:
        """Process a single audio file through the full pipeline.

        Uses the ReAct loop:
        1. Observe current state
        2. Think (decide next action)
        3. Act (execute tool)
        4. Loop until done

        Args:
            audio_path: Path to the audio file.

        Returns:
            AgentResult with all processing outputs.
        """
        path = Path(audio_path)
        result = AgentResult(filename=path.name)

        self._log(f"Starting processing: {path.name}")
        step = 0

        while True:
            step += 1
            action = self._think(result, step)

            if action is None:
                break

            self._log(f"Step {step}: {action}")

            try:
                self._act(action, result, audio_path)
            except Exception as e:
                error_msg = f"Error in {action}: {e}"
                self._log(error_msg)
                result.error = error_msg
                result.status = "error"

                # Store partial results even on error
                try:
                    self._csv_store.run(
                        filename=result.filename,
                        transcription=result.transcription,
                        translation=result.translation,
                        summary=result.summary,
                        status="error",
                    )
                except Exception:
                    pass

                break

        self._log(f"Finished: {result.filename} (status={result.status})")
        return result

    def process_batch(self, directory: str) -> list[AgentResult]:
        """Process all .opus files in a directory.

        Args:
            directory: Path to directory containing .opus files.

        Returns:
            List of AgentResult for each file.
        """
        dir_path = Path(directory)
        if not dir_path.is_dir():
            raise NotADirectoryError(f"Not a directory: {directory}")

        opus_files = sorted(dir_path.glob("*.opus"))
        if not opus_files:
            self._log(f"No .opus files found in {directory}")
            return []

        self._log(f"Found {len(opus_files)} .opus file(s)")
        results: list[AgentResult] = []

        for audio_file in opus_files:
            result = self.process(str(audio_file))
            results.append(result)

        return results

    def get_report(self) -> str:
        """Generate a text report from stored CSV data.

        Returns:
            Formatted report string.
        """
        stats = self._csv_store.get_stats()
        records = self._csv_store.read_all()

        lines = [
            "=" * 60,
            "STUDENT TRACKING REPORT",
            "=" * 60,
            f"Total records: {stats['total']}",
            f"Complete:      {stats['complete']}",
            f"Partial:       {stats['partial']}",
            f"Errors:        {stats['error']}",
            "-" * 60,
        ]

        for i, record in enumerate(records, 1):
            lines.append(f"\n--- Record {i} ---")
            lines.append(f"File:          {record.get('filename', 'N/A')}")
            lines.append(f"Timestamp:     {record.get('timestamp', 'N/A')}")
            lines.append(f"Status:        {record.get('status', 'N/A')}")

            transcription = record.get("transcription", "")
            if transcription:
                preview = transcription[:80] + "..." if len(transcription) > 80 else transcription
                lines.append(f"Transcription: {preview}")

            translation = record.get("translation", "")
            if translation:
                preview = translation[:80] + "..." if len(translation) > 80 else translation
                lines.append(f"Translation:   {preview}")

            summary = record.get("summary", "")
            if summary:
                lines.append(f"Summary:       {summary}")

        lines.append("\n" + "=" * 60)
        return "\n".join(lines)
