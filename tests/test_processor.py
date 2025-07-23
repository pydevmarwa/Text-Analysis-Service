import pytest
from app.processor import process_message

@pytest.mark.asyncio
async def test_process_message_score():
    input_msg = {
        "id": "1",
        "text": "This is a test message",
        "user_id": "user_123",
        "timestamp": "2025-07-17T12:00:00Z",
        "type": "update"
    }

    enriched = await process_message(input_msg)

    assert 0 <= enriched["toxicity_score"] <= 100
    assert enriched["action"] == "update"
    assert enriched["processed_at"] is not None
