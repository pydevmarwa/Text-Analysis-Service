import asyncio
import json
import aio_pika
from aio_pika import RobustConnection
from app.config import RABBITMQ
from app.processor import process_message
from app.db import save_to_mongodb
from app.publisher import publish_result

async def connect_with_retry(retries=10, delay=3) -> RobustConnection:
    """
    Connects to RabbitMQ with retry logic in case of failure.

    Args:
        retries (int): Number of retry attempts.
        delay (int): Delay in seconds between retries.

    Returns:
        RobustConnection: Established robust connection to RabbitMQ.
    """
    for attempt in range(1, retries + 1):
        try:
            print(f"Attempting to connect to RabbitMQ ({attempt}/{retries})...")
            connection: RobustConnection = await aio_pika.connect_robust(
                host=RABBITMQ["HOST"],
                port=RABBITMQ["PORT"],
                login=RABBITMQ["USER"],
                password=RABBITMQ["PASSWORD"],
            )
            print("Connected to RabbitMQ!")
            return connection
        except Exception as e:
            print(f"[!] Connection failed: {e}")
            if attempt == retries:
                raise
            await asyncio.sleep(delay)

async def handle_message(message: aio_pika.IncomingMessage):
    """
    Process a single incoming message from RabbitMQ.

    Args:
        message (aio_pika.IncomingMessage): Incoming message instance.
    """
    async with message.process(requeue=False):
        try:
            raw_body = message.body.decode()
            raw_data = json.loads(raw_body)
            print(f"[x] Received message: {raw_data.get('id')}")

            processed = await process_message(raw_data)
            await save_to_mongodb(processed)

            if processed.get("action") != "delete":
                await publish_result(processed)

        except json.JSONDecodeError:
            print("[!] Invalid JSON received.")
        except Exception as e:
            print(f"[!] Unexpected error during processing: {e}")

async def start_consumer():
    """
    Starts the RabbitMQ consumer to listen for incoming messages asynchronously.

    Returns:
        RobustConnection: The connection object to RabbitMQ.
    """
    connection = await connect_with_retry()
    channel = await connection.channel()

    # Process up to 20 messages concurrently
    await channel.set_qos(prefetch_count=20)

    queue = await channel.declare_queue(RABBITMQ["INPUT_QUEUE"], durable=True)
    print("[*] Waiting for messages... Press Ctrl+C to exit.")

    async def on_message(message: aio_pika.IncomingMessage):
        asyncio.create_task(handle_message(message))

    await queue.consume(on_message)
    return connection
