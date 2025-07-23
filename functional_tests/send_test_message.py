import asyncio
import aio_pika
import json
from datetime import datetime

RABBITMQ_HOST = 'localhost'  # or 'rabbitmq' if using Docker
RABBITMQ_PORT = 5672
RABBITMQ_USER = 'guest'
RABBITMQ_PASSWORD = 'guest'
INPUT_QUEUE = 'incoming_texts'

async def send_message(message):
    """
    Send a single message to the RabbitMQ input queue.
    """
    connection = await aio_pika.connect_robust(
        host=RABBITMQ_HOST,
        port=RABBITMQ_PORT,
        login=RABBITMQ_USER,
        password=RABBITMQ_PASSWORD,
    )
    async with connection:
        channel = await connection.channel()
        await channel.declare_queue(INPUT_QUEUE, durable=True)
        await channel.default_exchange.publish(
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
        {"id": "msg2", "user_id": "u2", "text": "Another comment", "timestamp": datetime.utcnow().isoformat(), "type": "delete"},
        {"id": "msg3", "type": "delete"},  # Delete message without extra fields
        # Add more messages as needed
    ]

    tasks = [send_message(msg) for msg in batch]
    await asyncio.gather(*tasks)
    print("All test messages sent.")

if __name__ == "__main__":
    asyncio.run(main())
