"""CSV storage tool for student tracking data."""

import csv
import os
from datetime import datetime
from pathlib import Path
from typing import Optional

from agent.config import Config


class CSVStoreTool:
    """Store processing results in a CSV file for student tracking."""

    name = "store"
    description = "Store transcription, translation, and summary results in CSV"

    FIELDNAMES = [
        "timestamp",
        "filename",
        "source_language",
        "transcription",
        "translation",
        "summary",
        "audio_duration_sec",
        "status",
    ]

    def __init__(self, config: Config) -> None:
        self._csv_path = Path(config.csv_path)
        self._ensure_csv()

    def _ensure_csv(self) -> None:
        """Create the CSV file with headers if it doesn't exist."""
        self._csv_path.parent.mkdir(parents=True, exist_ok=True)
        if not self._csv_path.exists():
            with open(self._csv_path, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=self.FIELDNAMES)
                writer.writeheader()

    def run(
        self,
        filename: str,
        transcription: str = "",
        translation: str = "",
        summary: str = "",
        source_language: str = "hi",
        audio_duration_sec: Optional[float] = None,
        status: str = "complete",
    ) -> str:
        """Store a processing result in the CSV file.

        Args:
            filename: Original audio filename.
            transcription: Transcribed text.
            translation: Translated text.
            summary: Summary text.
            source_language: Source language code.
            audio_duration_sec: Audio duration in seconds.
            status: Processing status (complete/partial/error).

        Returns:
            Confirmation message.
        """
        row = {
            "timestamp": datetime.now().isoformat(),
            "filename": filename,
            "source_language": source_language,
            "transcription": transcription,
            "translation": translation,
            "summary": summary,
            "audio_duration_sec": str(audio_duration_sec) if audio_duration_sec else "",
            "status": status,
        }

        with open(self._csv_path, "a", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=self.FIELDNAMES)
            writer.writerow(row)

        return f"Stored result for '{filename}' in {self._csv_path}"

    def read_all(self) -> list[dict[str, str]]:
        """Read all records from the CSV file.

        Returns:
            List of record dictionaries.
        """
        if not self._csv_path.exists():
            return []

        with open(self._csv_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            return list(reader)

    def get_stats(self) -> dict[str, int]:
        """Get summary statistics from stored data.

        Returns:
            Dictionary with counts by status.
        """
        records = self.read_all()
        stats: dict[str, int] = {
            "total": len(records),
            "complete": 0,
            "partial": 0,
            "error": 0,
        }
        for record in records:
            status = record.get("status", "unknown")
            if status in stats:
                stats[status] += 1
        return stats
