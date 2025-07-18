from datetime import datetime
from typing import Dict
from app.utils import simulate_heavy_processing, calculate_toxicity_score
from app.config import PROCESSING

async def process_message(raw_message: Dict) -> Dict:
    """
    Process raw RabbitMQ message to produce enriched message or deletion instruction.

    Args:
        raw_message (Dict): Raw input message from RabbitMQ.

    Returns:
        Dict: Enriched message with toxicity score or delete action.

    Raises:
        ValueError: If message type is unknown or required fields missing.
    """
    msg_type = str(raw_message.get('type', '')).lower()

    if msg_type == 'delete':
        return {
            'action': 'delete',
            'id': raw_message.get('id')
        }

    if msg_type == 'update':
        text = raw_message.get('text')
        if not text:
            raise ValueError("Missing 'text' field for update message")

        processing_time = await simulate_heavy_processing()
        toxicity_score = await calculate_toxicity_score(text)
        is_toxic = toxicity_score > PROCESSING['TOXICITY_THRESHOLD']

        return {
            'action': 'update',
            'id': raw_message.get('id'),
            'user_id': raw_message.get('user_id'),
            'original_text': text,
            'timestamp': raw_message.get('timestamp'),
            'processing_time': round(processing_time, 2),
            'toxicity_score': toxicity_score,
            'is_toxic': is_toxic,
            'processed_at': datetime.utcnow().isoformat()
        }

    raise ValueError(f"Unknown message type '{msg_type}'")
