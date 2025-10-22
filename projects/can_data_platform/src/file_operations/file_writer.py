"""File writing operations with atomic operations."""

import json
import logging
import os
from abc import ABC, abstractmethod
from typing import Dict, List, Any


logger = logging.getLogger(__name__)


class FileWriter(ABC):
    """Abstract base class for file writers."""

    @abstractmethod
    def write(self, events: List[Dict[str, Any]], output_path: str) -> None:
        """Write events to file.

        Args:
            events: List of event dictionaries
            output_path: Path to output file
        """
        raise NotImplementedError


class JSONLFileWriter(FileWriter):
    """JSONL file writer with atomic operations.

    Follows Single Responsibility Principle by focusing only on file writing.
    """

    def write(self, events: List[Dict[str, Any]], output_path: str) -> None:
        """Write events to JSONL file with atomic operation.

        Args:
            events: List of event dictionaries
            output_path: Path to output JSONL file

        Raises:
            OSError: If file operations fail
            IOError: If file writing fails
        """
        logger.info("Writing %d events to file: %s", len(events), output_path)

        # Ensure directory exists
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        # Write with atomic operation (write to temp file, then rename)
        temp_path = f"{output_path}.tmp"

        try:
            self._write_to_temp_file(events, temp_path)
            self._atomic_move(temp_path, output_path)

            logger.info("Successfully wrote %d events to %s", len(events), output_path)

        except (OSError, IOError) as e:
            logger.error("Failed to write events to file %s: %s", output_path, e)
            self._cleanup_temp_file(temp_path)
            raise

    def _write_to_temp_file(self, events: List[Dict[str, Any]], temp_path: str) -> None:
        """Write events to temporary file."""
        with open(temp_path, "w", encoding="utf-8") as f:
            for event in events:
                json.dump(event, f, separators=(',', ':'))  # Compact JSON
                f.write('\n')

    def _atomic_move(self, temp_path: str, output_path: str) -> None:
        """Atomically move temp file to final location."""
        if os.path.exists(output_path):
            os.remove(output_path)
        os.rename(temp_path, output_path)

    def _cleanup_temp_file(self, temp_path: str) -> None:
        """Clean up temporary file if it exists."""
        if os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except OSError:
                pass  # Ignore cleanup errors


class FileWriterFactory:
    """Factory for creating file writers."""

    @staticmethod
    def create_jsonl_writer() -> JSONLFileWriter:
        """Create a JSONL file writer."""
        return JSONLFileWriter()
