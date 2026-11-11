import asyncio
import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


class StorageError(Exception):
    """Raised when data can't be read from or written to storage."""


class JsonStorage:
    def __init__(self, filepath: Path | str):
        self.filepath = Path(filepath)
        self._write_lock = asyncio.Lock()   


    def _read_sync(self) -> list[dict]:
        with open(self.filepath, "r", encoding="utf-8") as f:
            return json.load(f)

    def _write_sync(self, data: list[dict]) -> None:
        self.filepath.parent.mkdir(parents=True, exist_ok=True)
        tmp = self.filepath.with_suffix(self.filepath.suffix + ".tmp")
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)
        tmp.replace(self.filepath)          

    async def load(self) -> list[dict]:
        try:
            data = await asyncio.to_thread(self._read_sync)
        except FileNotFoundError:           
            logger.info("No data file yet at %s, starting empty", self.filepath)
            return []
        except json.JSONDecodeError as e:
            logger.exception("Data file is not valid JSON: %s", self.filepath)
            raise StorageError("Saved expenses file is corrupted.") from e
        except OSError as e:
            logger.exception("Could not read %s", self.filepath)
            raise StorageError("Could not read the saved expenses file.") from e

        if not isinstance(data, list):
            logger.error("Unexpected data shape in %s: %s", self.filepath, type(data).__name__)
            raise StorageError("Saved expenses file has an unexpected format.")

        logger.info("Loaded %d records from %s", len(data), self.filepath)
        return data

    async def save(self, data: list[dict]) -> None:
        async with self._write_lock:
            try:
                await asyncio.to_thread(self._write_sync, data)
            except (OSError, TypeError) as e:
                logger.exception("Failed to write %s", self.filepath)
                raise StorageError("Could not save expenses.") from e
        logger.info("Saved %d records to %s", len(data), self.filepath)