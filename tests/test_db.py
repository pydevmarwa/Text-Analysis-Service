import pytest
from unittest.mock import AsyncMock
from app.db import MongoDBManager

@pytest.mark.asyncio
async def test_save_or_update():
    mock_collection = AsyncMock()
    db_manager = MongoDBManager()
    db_manager.collection = mock_collection

    test_data = {
        "id": "1",
        "text": "test",
        "user_id": "user_1",
        "score": 88
    }

    await db_manager.save_or_update(test_data)
    mock_collection.update_one.assert_awaited_once_with(
        {"id": "1"},
        {"$set": test_data},
        upsert=True
    )

@pytest.mark.asyncio
async def test_delete():
    mock_collection = AsyncMock()
    db_manager = MongoDBManager()
    db_manager.collection = mock_collection

    await db_manager.delete("1")
    mock_collection.delete_one.assert_awaited_once_with({"id": "1"})
