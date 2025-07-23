import pytest
import json
from unittest.mock import AsyncMock, patch
from app.consumer import handle_message

class FakeIncomingMessage:
    """
    Fake IncomingMessage for testing handle_message.
    Provides .body and a synchronous .process() method returning an async context manager.
    """
    def __init__(self, body: bytes):
        # body should be raw bytes
        self.body = body if isinstance(body, bytes) else body.encode()

    def process(self, requeue=False):
        class DummyContext:
            async def __aenter__(self_inner):
                return self_inner
            async def __aexit__(self_inner, exc_type, exc, tb):
                return False
        return DummyContext()

@pytest.mark.asyncio
@patch("app.consumer.save_to_mongodb", new_callable=AsyncMock)
@patch("app.consumer.publish_result", new_callable=AsyncMock)
async def test_handle_update_message(mock_publish, mock_save):
    # Prepare raw message data for update
    raw_msg = {
        "id": "99",
        "text": "unit test message",
        "user_id": "user_x",
        "timestamp": "2025-07-18T12:00:00Z",
        "type": "update"
    }
    body = json.dumps(raw_msg)
    fake_message = FakeIncomingMessage(body)

    # Call handle_message
    await handle_message(fake_message)

    # Ensure save_to_mongodb was called once with processed data
    assert mock_save.await_count == 1, "save_to_mongodb should be awaited once"
    # Ensure publish_result was called once
    assert mock_publish.await_count == 1, "publish_result should be awaited once"
