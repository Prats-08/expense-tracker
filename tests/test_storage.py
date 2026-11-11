import asyncio
import json
import logging

import pytest

from storage import JsonStorage, StorageError


async def test_load_missing_file_returns_empty_list(storage):
    assert await storage.load() == []


async def test_save_then_load_round_trip(storage):
    data = [{"amount": 1, "category": "Food", "description": "x", "date": "2026-11-01"}]
    await storage.save(data)
    assert await storage.load() == data


async def test_save_writes_indented_json(storage):
    await storage.save([{"a": 1}])
    assert "\n    " in storage.filepath.read_text()   # indent=4


async def test_save_creates_parent_directories(tmp_path):
    s = JsonStorage(tmp_path / "a" / "b" / "expenses.json")
    await s.save([])
    assert s.filepath.exists()


async def test_save_is_atomic_no_tmp_file_left(storage):
    await storage.save([{"a": 1}])
    assert [p.name for p in storage.filepath.parent.iterdir()] == ["expenses.json"]


async def test_failed_save_keeps_old_data_intact(storage):
    await storage.save([{"keep": "me"}])

    with pytest.raises(StorageError):
        await storage.save([{"bad": {1, 2, 3}}])      # a set is not JSON serialisable

    assert json.loads(storage.filepath.read_text()) == [{"keep": "me"}]


async def test_save_unserialisable_raises_storage_error_with_cause(storage):
    with pytest.raises(StorageError) as exc_info:
        await storage.save([{"bad": object()}])
    assert isinstance(exc_info.value.__cause__, TypeError)


async def test_save_to_impossible_path_raises_storage_error(tmp_path):
    blocker = tmp_path / "blocker"
    blocker.write_text("file")
    s = JsonStorage(blocker / "expenses.json")
    with pytest.raises(StorageError, match="Could not save"):
        await s.save([])


async def test_load_invalid_json_raises_storage_error(storage, caplog):
    storage.filepath.write_text("not json")
    with caplog.at_level(logging.ERROR, logger="storage"):
        with pytest.raises(StorageError, match="corrupted"):
            await storage.load()
    assert "not valid JSON" in caplog.text


@pytest.mark.parametrize("payload", ['{"amount": 1}', '"just a string"', "42", "null"])
async def test_load_non_list_json_raises_storage_error(storage, payload):
    storage.filepath.write_text(payload)
    with pytest.raises(StorageError, match="unexpected format"):
        await storage.load()


async def test_load_directory_instead_of_file_raises_storage_error(tmp_path):
    s = JsonStorage(tmp_path)         
    with pytest.raises(StorageError, match="Could not read"):
        await s.load()


async def test_accepts_str_path(tmp_path):
    s = JsonStorage(str(tmp_path / "x.json"))
    await s.save([])
    assert await s.load() == []


async def test_concurrent_saves_leave_a_valid_file(storage):
    payloads = [[{"n": i}] for i in range(20)]
    await asyncio.gather(*(storage.save(p) for p in payloads))

    final = json.loads(storage.filepath.read_text())   
    assert final in payloads