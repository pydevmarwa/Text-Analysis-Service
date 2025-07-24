import asyncio
import aio_pika
import json
from datetime import datetime
from app.config import RABBITMQ

INPUT_QUEUE = RABBITMQ['INPUT_QUEUE']
OUTPUT_QUEUE = RABBITMQ['OUTPUT_QUEUE']

async def send_message(message):
    """
    Send a single message to the RabbitMQ input queue.
    """
    conn = await aio_pika.connect_robust(
        host=RABBITMQ['HOST'], port=RABBITMQ['PORT'],
        login=RABBITMQ['USER'], password=RABBITMQ['PASSWORD']
    )
    async with conn:
        ch = await conn.channel()
        await ch.declare_queue(INPUT_QUEUE,
                               durable=True,
                               arguments={
                                   "x-dead-letter-exchange": RABBITMQ['DLX_EXCHANGE']
                               }
                               )
        await ch.default_exchange.publish(
            aio_pika.Message(
                body=json.dumps(message).encode(),
                delivery_mode=aio_pika.DeliveryMode.PERSISTENT
            ),
            routing_key=INPUT_QUEUE,
        )

async def main():
    """
    Sends a batch of example update and delete messages.
    """
    batch = [
        {"id": "msg1", "user_id": "u1", "text": "Hello world", "timestamp": datetime.utcnow().isoformat(), "type": "update"},
        {"id": "msg2", "user_id": "u2", "text": "Another comment", "timestamp": datetime.utcnow().isoformat(), "type": "update"},
        {"id": "msg3", "type": "delete"},  # Delete message without extra fields
        # Add more messages as needed
    ]

    tasks = [send_message(msg) for msg in batch]
    await asyncio.gather(*tasks)
    print("All test messages sent.")

if __name__ == "__main__":
    asyncio.run(main())
