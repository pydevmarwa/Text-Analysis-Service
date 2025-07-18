import asyncio
import aio_pika
import json

RABBITMQ_HOST = 'localhost'  # or 'rabbitmq' if using Docker
RABBITMQ_PORT = 5672
RABBITMQ_USER = 'guest'
RABBITMQ_PASSWORD = 'guest'
OUTPUT_QUEUE = 'processed_texts'

async def consume_processed():
    """
    Consume messages from the output queue and print them.
    """
    connection = await aio_pika.connect_robust(
        host=RABBITMQ_HOST,
        port=RABBITMQ_PORT,
        login=RABBITMQ_USER,
        password=RABBITMQ_PASSWORD
    )
    async with connection:
        channel = await connection.channel()
        queue = await channel.declare_queue(OUTPUT_QUEUE, durable=True)

        print(f"[*] Waiting for messages in '{OUTPUT_QUEUE}'...")

        async with queue.iterator() as queue_iter:
            async for message in queue_iter:
                async with message.process():
                    body = message.body.decode()
                    data = json.loads(body)
                    print(f"[x] Processed message received: {data}")

if __name__ == "__main__":
    asyncio.run(consume_processed())
